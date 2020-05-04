"""The H API service."""

import json

import requests
from h_api.bulk_api import BulkAPI, CommandBuilder
from requests import RequestException

from lms.models import HUser
from lms.services import HAPIError, HAPINotFoundError

__all__ = ["HAPI"]


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

    # pylint: disable=too-many-arguments
    # (data will be removed soon)
    def _api_request(self, method, path, data=None, headers=None, body=None):
        """
        Send any kind of HTTP request to the h API and return the response.

        :param method: the HTTP request method to use, for example "GET",
                       "POST", "PUT", "PATCH" or "DELETE"
        :param path: the h API path to post to, relative to
                     ``settings["h_api_url_private"]``, for example:
                     ``"users"`` or ``"groups/<GROUPID>/members/<USERID>"``
        :param data: the data to post as JSON in the request body
        :param body: the body to send as a string (without modification)
        :param headers: extra headers to pass with the request

        :raise HAPINotFoundError: If the request fails with 404
        :raise HAPIError: if the request fails for any other reason
        :return: the response from the h API
        :rtype: requests.Response
        """
        headers = headers or {}
        headers["Hypothesis-Application"] = "lms"

        request_args = {"headers": headers}

        if body is not None:
            request_args["data"] = body
        elif data is not None:
            request_args["data"] = json.dumps(data, separators=(",", ":"))

        try:
            response = requests.request(
                method=method,
                url=self._base_url + path.lstrip("/"),
                auth=self._http_auth,
                timeout=10,
                **request_args,
            )
            response.raise_for_status()

        except RequestException as err:
            response = getattr(err, "response", None)
            status_code = getattr(response, "status_code", None)

            if status_code == 404:
                raise HAPINotFoundError(
                    "Could not find requested resource", response
                ) from err

            raise HAPIError("Connecting to Hypothesis failed", response) from err

        return response
