"""Hypothesis API service."""
import json

import requests
from requests import RequestException

from lms.services import HAPIError
from lms.services import HAPINotFoundError


__all__ = ["HypothesisAPIService"]


class HypothesisAPIService:
    """
    Low-level API service.

    A service that provides low-level methods for calling the Hypothesis API
    with builtin error handling. This service provides HTTP verb methods like
    ``get()`` and ``post()``. Other services can be built on top of this one
    and provide higher-level methods like ``create_user()`` or
    ``update_group()``.
    """

    def __init__(self, _context, request):
        """
        Return a new HypothesisAPIService object.

        :arg _context: the Pyramid context resource
        :arg request: the Pyramid request
        :type request: pyramid.request.Request
        """
        settings = request.registry.settings

        self._client_id = settings["h_client_id"]
        self._client_secret = settings["h_client_secret"]
        self._authority = settings["h_authority"]
        self._base_url = settings["h_api_url_private"]

    def delete(self, *args, **kwargs):
        """
        Send a DELETE request to the h API and return the response.

        See :meth:`request` for details.
        """
        return self.request("DELETE", *args, **kwargs)

    def get(self, *args, **kwargs):
        """
        Send a GET request to the h API and return the response.

        See :meth:`request` for details.
        """
        return self.request("GET", *args, **kwargs)

    def patch(self, *args, **kwargs):
        """
        Send a PATCH request to the h API and return the response.

        See :meth:`request` for details.
        """
        return self.request("PATCH", *args, **kwargs)

    def post(self, *args, **kwargs):
        """
        Send a POST request to the h API and return the response.

        See :meth:`request` for details.
        """
        return self.request("POST", *args, **kwargs)

    def put(self, *args, **kwargs):
        """
        Send a PUT request to the h API and return the response.

        See :meth:`request` for details.
        """
        return self.request("PUT", *args, **kwargs)

    def request(
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
            if status_code == 404:
                exception_class = HAPINotFoundError
            else:
                exception_class = HAPIError
            if status_code is None or status_code not in statuses:
                raise exception_class(
                    explanation="Connecting to Hypothesis failed", response=response
                ) from err

        return response
