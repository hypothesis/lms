"""The H API service."""

import itertools
import json
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TypedDict

from h_api.bulk_api import BulkAPI, CommandBuilder

from lms.models import HUser
from lms.services.exceptions import ExternalRequestError
from lms.services.http import HTTPService


class AnnotationCounts(TypedDict):
    annotations: int
    replies: int
    page_notes: int
    last_activity: str

    assignment_id: str | None
    display_name: str | None
    userid: str | None


class HAPIError(ExternalRequestError):
    """
    A problem with an h API request.

    Raised whenever an h API request times out or when an unsuccessful, invalid
    or unexpected response is received from the h API.
    """


def _rfc3339_format(date: datetime) -> str:
    """
    Convert a datetime object to an RFC3339 datetime format string.

    Which looks like: 2018-11-13T20:20:39+00:00
    """
    if not date.tzinfo:
        date = date.replace(tzinfo=UTC)

    return date.isoformat()


class HAPI:
    """
    A client for the "h" API.

    :raise HAPIError: if a call to the "h" API raises an unhandled exception
    """

    @dataclass
    class HAPIGroup:
        authority_provided_id: str

    def __init__(
        self,
        authority,
        client_id,
        client_secret,
        h_private_url,
        http_service: HTTPService,
    ):
        self._authority = authority
        self._http_auth = (client_id, client_secret)
        self._base_url = h_private_url
        self._http_service = http_service

    def execute_bulk(self, commands):
        """
        Send a series of h_api commands to the H bulk API.

        :param commands: Instances of h_api Commands
        """

        commands = list(commands)
        commands = [  # noqa: RUF005
            CommandBuilder.configure(
                effective_user=HUser(username="lms").userid(self._authority),
                total_instructions=len(commands) + 1,
            )
        ] + commands

        self._api_request(
            "POST",
            path="bulk",
            body=BulkAPI.to_string(commands),
            headers={"Content-Type": "application/vnd.hypothesis.v1+x-ndjson"},
        )

    def get_user(self, username):
        """
        Return the h user for the given username.

        :rtype: HUser
        """
        userid = HUser(username).userid(self._authority)
        user_info = self._api_request("GET", path=f"users/{userid}").json()

        return HUser(username=username, display_name=user_info["display_name"])

    def get_annotations(
        self,
        h_userid: str,
        created_after: datetime,
        created_before: datetime,
    ) -> Iterator[dict]:
        """
        Get an iterator of annotation objects for the specified h_userid.

        This is an iterator of annotations viewable by the provided h_userid.

        :param h_userid: h_userid
        :param created_after: Datetime to search after
        :param created_before: Datetime to search before
        """
        username = self.get_username(h_userid)

        payload = {
            "filter": {
                "limit": 100000,
                "username": username,
                "created": {
                    "gt": _rfc3339_format(created_after),
                    "lte": _rfc3339_format(created_before),
                },
            },
        }

        with self._api_request(
            "POST",
            path="bulk/annotation",
            body=json.dumps(payload),
            headers={
                "Content-Type": "application/vnd.hypothesis.v1+json",
                "Accept": "application/vnd.hypothesis.v1+x-ndjson",
            },
            stream=True,
        ) as response:
            for line in response.iter_lines():
                annotation = json.loads(line)
                author = annotation.get("author")
                if author:  # noqa: SIM102
                    if "username" in author and "userid" not in author:
                        author["userid"] = self.get_userid(author["username"])
                yield annotation

    def get_groups(
        self,
        groups: Sequence[str],
        annotations_created_after: datetime,
        annotations_created_before: datetime,
        batch_size: int = 250,
    ) -> Iterator[HAPIGroup]:
        """
        Fetch groups that have annotations created between two dates.

        It will make one API request per `batch_size` candidate groups.
        """
        for batch in self._batched(groups, batch_size):
            payload = {
                "filter": {
                    "groups": batch,
                    "annotations_created": {
                        "gt": _rfc3339_format(annotations_created_after),
                        "lte": _rfc3339_format(annotations_created_before),
                    },
                },
            }

            with self._api_request(
                "POST",
                path="bulk/group",
                body=json.dumps(payload),
                headers={
                    "Content-Type": "application/vnd.hypothesis.v1+json",
                    "Accept": "application/vnd.hypothesis.v1+x-ndjson",
                },
                stream=True,
            ) as response:
                for line in response.iter_lines():
                    group = json.loads(line)
                    yield self.HAPIGroup(
                        authority_provided_id=group["authority_provided_id"]
                    )

    def get_annotation_counts(
        self,
        group_authority_ids: list[str],
        group_by: str,
        h_userids: list[str] | None = None,
        resource_link_ids: list[str] | None = None,
    ) -> list[AnnotationCounts]:
        if not group_authority_ids:
            return []

        filters = {
            "groups": group_authority_ids,
            "assignment_ids": resource_link_ids,
        }
        if h_userids:
            filters["h_userids"] = h_userids

        response = self._api_request(
            "POST",
            path="bulk/lms/annotations",
            body=json.dumps({"group_by": group_by, "filter": filters}),
            headers={
                "Content-Type": "application/vnd.hypothesis.v1+json",
            },
            stream=False,
        )
        return response.json()

    def _api_request(self, method, path, body=None, headers=None, stream=False):  # noqa: FBT002
        """
        Send any kind of HTTP request to the h API and return the response.

        :param method: the HTTP request method to use, (e.g. "GET")
        :param path: the h API path to post to, relative to
                     `settings["h_api_url_private"]` (e.g. "users")
        :param body: the body to send as a string (without modification)
        :param headers: extra headers to pass with the request

        :raise HAPIError: if the request fails for any other reason
        :return: the response from the h API
        :rtype: requests.Response
        """
        headers = headers or {}
        headers["Hypothesis-Application"] = "lms"

        request_args = {}
        if body is not None:
            request_args["data"] = body

        try:
            response = self._http_service.request(
                method=method,
                url=self._base_url + path.lstrip("/"),
                auth=self._http_auth,
                headers=headers,
                stream=stream,
                timeout=(60, 60),
                **request_args,
            )
        except ExternalRequestError as err:
            raise HAPIError("Connecting to Hypothesis failed", err.response) from err  # noqa: EM101, TRY003

        return response

    def get_userid(self, username):
        """Return the h userid for the given username and authority."""
        return HUser(username).userid(self._authority)

    def get_username(self, userid):
        """
        Return the h username for the given userid.

        For example if userid is 'acct:seanh@hypothes.is' then return 'seanh'.

        :raises ValueError: if the given userid isn't valid
        """
        match = re.match(r"^acct:([^@]+)@(.*)$", userid)
        if match:
            return match.groups()[0]

        raise ValueError(userid)

    @staticmethod
    def _batched(iterable, n):
        """Batch data from the iterable into tuples of length n. The last batch may be shorter than n.

        This is part of itertools in python 3.12

        https://docs.python.org/3/library/itertools.html#itertools.batched
        """
        iterator = iter(iterable)
        while batch := tuple(itertools.islice(iterator, n)):
            yield batch


def service_factory(_context, request) -> HAPI:
    """Get a new instance of HAPI service."""

    settings = request.registry.settings

    return HAPI(
        authority=settings["h_authority"],
        client_id=settings["h_client_id"],
        client_secret=settings["h_client_secret"],
        h_private_url=settings["h_api_url_private"],
        http_service=request.find_service(name="http"),
    )
