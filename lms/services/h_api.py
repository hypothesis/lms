import json

import requests
from requests import RequestException

from lms.services import HAPIError, HAPINotFoundError
from lms.values import HUser

__all__ = ["HAPIClient"]


class HAPIClient:
    """
    High-level h API service.

    This service supports high-level operations (eg. fetching a user) on h
    resources via the low-level "hapi" client.

    :raises HAPIError: On any unhandled exception during calls to the H API
    """

    def __init__(self, _context, request):
        self._request = request

        settings = request.registry.settings

        self._client_id = settings["h_client_id"]
        self._client_secret = settings["h_client_secret"]
        self._authority = settings["h_authority"]
        self._base_url = settings["h_api_url_private"]

    def get_user(self, username):
        """
        Fetch an `HUser` given their username.

        :rtype: HUser
        """
        authority = self._request.registry.settings["h_authority"]
        userid = HUser(authority, username).userid
        user_info = self._request("GET", path=f"users/{userid}").json()

        return HUser(
            authority=authority,
            username=username,
            display_name=user_info["display_name"],
        )

    def create_user(self, h_user, provider, provider_unique_id):
        user_data = {
            "username": h_user.username,
            "display_name": h_user.display_name,
            "authority": self._request.registry.settings["h_authority"],
            "identities": [
                {"provider": provider, "provider_unique_id": provider_unique_id,}
            ],
        }

        self._request("POST", "users", user_data)

    def update_user(self, h_user):
        """

        :param h_user:
        :return:
        """
        self._request(
            "PATCH", f"users/{h_user.username}", {"display_name": h_user.display_name},
        )

    def upsert_user(self, h_user, provider, provider_unique_id):
        try:
            self.update_user(h_user)
        except HAPINotFoundError:
            self.create_user(h_user, provider, provider_unique_id)

    def create_group(self, group_id, group_name, h_user):
        self._request(
            "PUT",
            f"groups/{group_id}",
            {"groupid": group_id, "name": group_name,},
            user_id=h_user.userid,
        )

    def update_group(self, group_id, group_name):
        """

        :param group_id:
        :param group_name:
        :return:
        """
        self._request(
            "PATCH", f"groups/{group_id}", {"name": group_name},
        )

    def add_user_to_group(self, h_user, group_id):
        """

        :param h_user:
        :param group_id:
        :return:
        """
        self._request("POST", f"groups/{group_id}/members/{h_user.userid}")

    def _request(
        self, method, path, data=None, userid=None, statuses=None
    ):  # pylint:disable=too-many-arguments
        """
        Send any kind of HTTP request to the h API and return the response.

        If the request fails for any reason (for example a network connection error
        or a timeout) :exc:`~lms.services.HAPIError` is raised.
        :exc:`~lms.services.HAPIError` is also raised if a 4xx or 5xx response is
        received. Use the optional keyword argument ``statuses`` to supply a list
        of one or more 4xx or 5xx statuses for which :exc:`~lms.services.HAPIError`
        should not be raised -- the 4xx or 5xx response will be returned instead.

        :arg method: the HTTP request method to use, for example "GET", "POST",
          "PUT", "PATCH" or "DELETE"
        :type method: str
        :arg path: the h API path to post to, relative to
          ``settings["h_api_url_private"]``, for example: ``"users"`` or
          ``"groups/<GROUPID>/members/<USERID>"``
        :type path: str
        :arg data: the data to post as JSON in the request body
        :type data: dict
        :arg userid: the userid of the user to post as (using an
          X-Forwarded-User header)
        :type userid: str
        :arg statuses: the list of 4xx and 5xx statuses that should not trigger an
          exception, for example: ``[409, 410]``
        :type statuses: list of ints

        :raise ~lms.services.HAPIError: if the request fails for any reason,
          including if a 4xx or 5xx response is received

        :return: the response from the h API
        :rtype: requests.Response
        """
        statuses = statuses or []

        request_args = {"headers": {"Hypothesis-Application": "lms"}}

        if path.startswith("/"):
            path = path[1:]

        if data is not None:
            request_args["data"] = json.dumps(data)

        if userid is not None:
            request_args["headers"]["X-Forwarded-User"] = userid

        try:
            response = requests.request(
                method=method,
                url=self._base_url + path,
                auth=(self._client_id, self._client_secret),
                timeout=10,
                **request_args,
            )
            response.raise_for_status()

        except RequestException as err:
            response = getattr(err, "response", None)
            status_code = getattr(response, "status_code", None)

            if status_code is None or status_code not in statuses:
                exception_class = HAPINotFoundError if status_code == 404 else HAPIError

                raise exception_class(
                    explanation="Connecting to Hypothesis failed", response=response
                ) from err

        return response
