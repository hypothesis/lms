"""The H API service."""

import json

import requests
from requests import RequestException

from lms.services import HAPIError, HAPINotFoundError
from lms.values import HUser

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

    def get_user(self, username):
        """
        Return the h user for the given username.

        :rtype: HUser
        """
        userid = HUser(self._authority, username).userid
        user_info = self._api_request("GET", path=f"users/{userid}").json()

        return HUser(
            authority=self._authority,
            username=username,
            display_name=user_info["display_name"],
        )

    def create_user(self, h_user, provider, provider_unique_id):
        """
        Create a user in H.

        :arg h_user: the user to be created in h
        :type h_user: HUser
        :param provider: the "provider" string to send to h
        :param provider_unique_id:  the "provider_unique_id" string to send to h
        """
        user_data = {
            "username": h_user.username,
            "display_name": h_user.display_name,
            "authority": self._authority,
            "identities": [
                {"provider": provider, "provider_unique_id": provider_unique_id,}
            ],
        }

        self._api_request("POST", "users", data=user_data)

    def create_lms_user(self):
        self.create_user(
            HUser(authority=self._authority, username="lms"),
            provider="lms",
            provider_unique_id="lms",
        )

    def update_user(self, h_user):
        """
        Update details for a user in H.

        Currently this only updates the display name.

        :param h_user: the updated user details to send to h
        :type h_user: HUser
        """
        self._api_request(
            "PATCH",
            f"users/{h_user.username}",
            data={"display_name": h_user.display_name},
        )

    def upsert_user(self, h_user, provider, provider_unique_id):
        """
        Create or update a user in H as appropriate.

        This is equivalent to calling `update_user()` then `create_user()` if
        that fails.

        :param h_user: the updated user value
        :type h_user: HUser
        :param provider: the "provider" string to send to h
        :param provider_unique_id:  the "provider_unique_id" string to send to h
        """
        try:
            self.update_user(h_user)
        except HAPINotFoundError:
            self.create_user(h_user, provider, provider_unique_id)

    def create_group(self, group_id, group_name):
        """
        Create a group in H.

        :param group_id: The id of the group
        :param group_name: The display name for the group
        """
        self._api_request(
            "PUT",
            f"groups/{group_id}",
            data={"groupid": group_id, "name": group_name},
            headers={"X-Forwarded-User": "acct:lms@lms.hypothes.is"},
        )

    def update_group(self, group_id, group_name):
        """
        Update a group in H.

        Currently this only updates the name of the group.

        :param group_id: The id of the group
        :param group_name: The display name for the group
        """
        self._api_request(
            "PATCH", f"groups/{group_id}", data={"name": group_name},
        )

    def add_user_to_groups(self, h_user, group_id):
        """
        Add the user as a member of the group.

        :param h_user: the user to add to the group
        :type h_user: HUser
        :param group_id: The id of the group
        """
        self._api_request("POST", f"groups/{group_id}/members/{h_user.userid}")

    def _api_request(self, method, path, data=None, headers=None):
        """
        Send any kind of HTTP request to the h API and return the response.

        :param method: the HTTP request method to use, for example "GET",
                       "POST", "PUT", "PATCH" or "DELETE"
        :param path: the h API path to post to, relative to
                     ``settings["h_api_url_private"]``, for example:
                     ``"users"`` or ``"groups/<GROUPID>/members/<USERID>"``
        :param data: the data to post as JSON in the request body
        :param headers: extra headers to pass with the request

        :raise HAPINotFoundError: If the request fails with 404
        :raise HAPIError: if the request fails for any other reason
        :return: the response from the h API
        :rtype: requests.Response
        """
        headers = headers or {}
        headers["Hypothesis-Application"] = "lms"

        request_args = {"headers": headers}

        if data is not None:
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
