"""The H API service."""
from dataclasses import dataclass

from h_api.bulk_api import BulkAPI, CommandBuilder

from lms.models import HUser
from lms.services.exceptions import ExternalRequestError


class HAPIError(ExternalRequestError):
    """
    A problem with an h API request.

    Raised whenever an h API request times out or when an unsuccessful, invalid
    or unexpected response is received from the h API.
    """


@dataclass(frozen=True)
class User:
    username: str


@dataclass(frozen=True)
class Group:
    authority_provided_id: str


@dataclass(frozen=True)
class Annotation:
    user: User
    group: Group


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

    def get_annotations(self, users, since, until):  # pylint:disable=unused-argument
        """
        Return the list of annotations for the given users and time range.

        Returns all annotations whose updated time is within the given time
        range and that are in groups of which any of the given users is a
        member.
        """
        return [
            Annotation(
                user=User(username="user_1"),
                group=Group(
                    authority_provided_id="d2871e5e1c36b58f207d9ef5b22dcb7829f52e61"
                ),
            ),
            Annotation(
                user=User(username="user_1"),
                group=Group(
                    authority_provided_id="f453c6124e4ead4471896f26e896c3e5bbf0bb36"
                ),
            ),
            Annotation(
                user=User(username="user_2"),
                group=Group(
                    authority_provided_id="83e64baad215f63057387910a1b41debc716a150"
                ),
            ),
            Annotation(
                user=User(username="user_1"),
                group=Group(
                    authority_provided_id="83e64baad215f63057387910a1b41debc716a150"
                ),
            ),
            Annotation(
                user=User(username="user_2"),
                group=Group(
                    authority_provided_id="83e64baad215f63057387910a1b41debc716a150"
                ),
            ),
        ]

    def get_user(self, username):
        """
        Return the h user for the given username.

        :rtype: HUser
        """
        userid = HUser(username).userid(self._authority)
        user_info = self._api_request("GET", path=f"users/{userid}").json()

        return HUser(username=username, display_name=user_info["display_name"])

    def _api_request(self, method, path, body=None, headers=None):
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
                **request_args,
            )
        except ExternalRequestError as err:
            raise HAPIError("Connecting to Hypothesis failed", err.response) from err

        return response
