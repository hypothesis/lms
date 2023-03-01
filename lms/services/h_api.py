"""The H API service."""
import json
from datetime import datetime, timezone
from typing import Iterator, List

from h_api.bulk_api import BulkAPI, CommandBuilder

from lms.models import HUser
from lms.services.exceptions import ExternalRequestError


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
        date = date.replace(tzinfo=timezone.utc)

    return date.isoformat()


class HAPI:
    """
    A client for the "h" API.

    :raise HAPIError: if a call to the "h" API raises an unhandled exception
    """

    def __init__(self, _context, request):
        self._request = request

        settings = request.registry.settings

        self._authority = settings["h_authority"]
        self._http_auth = (settings["h_client_id"], settings["h_client_secret"])
        self._base_url = settings["h_api_url_private"]
        self._http_service = request.find_service(name="http")

    def execute_bulk(self, commands):
        """
        Send a series of h_api commands to the H bulk API.

        :param commands: Instances of h_api Commands
        """

        commands = list(commands)
        commands = [
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
        audience_usernames: List[str],
        updated_after: datetime,
        updated_before: datetime,
    ) -> Iterator[dict]:
        """
        Get an iterator of annotation objects for the specified audience.

        This is an iterator of annotations viewable by _any_ of the provided
        usernames. It is your responsibility to work out who can see what, by
        knowing which groups users are in.

        :param audience_usernames: List of usernames (without `acct:...`)
        :param updated_after: Datetime to search after
        :param updated_before: Datetime to search before
        """
        payload = {
            "filter": {
                "limit": 100000,
                "audience": {"username": audience_usernames},
                "updated": {
                    "gt": _rfc3339_format(updated_after),
                    "lte": _rfc3339_format(updated_before),
                },
            },
            "fields": ["author.username", "group.authority_provided_id"],
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
                yield json.loads(line)

    def _api_request(self, method, path, body=None, headers=None, stream=False):
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
                **request_args,
            )
        except ExternalRequestError as err:
            raise HAPIError("Connecting to Hypothesis failed", err.response) from err

        return response
