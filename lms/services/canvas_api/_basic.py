"""Low level access to the Canvas API."""

from copy import deepcopy
from urllib.parse import urlencode

import requests
from requests import RequestException, Response, Session

from lms.services.exceptions import CanvasAPIError, ExternalRequestError


class BasicClient:
    """
    Provides low level access to the Canvas API.

    Also supports:

     * Pagination
     * Apply schema to responses
    """

    PAGINATION_PER_PAGE = 1000
    """The number of items to request at one time.

     This only applies for calls which return more than one, and is subject
     to a secret internal limit applied by Canvas (might be 100?)."""

    PAGINATION_MAXIMUM_REQUESTS = 25
    """The maximum number of calls to make before giving up."""

    def __init__(self, canvas_host, session=None):
        """
        Create a new BasicClient for making calls to the Canvas API.

        :param canvas_host: Hostname of the Canvas instance
        :param session: The requests Session to use
        :type session: requests.Session
        """

        # This is a requests Session object, not a DB session etc.
        self._session = session or Session()
        self._canvas_host = canvas_host

    def send(  # noqa: PLR0913
        self,
        method,
        path,
        schema,
        timeout,
        params=None,
        headers=None,
        url_stub="/api/v1",
    ) -> list:
        """
        Make a request to the Canvas API and apply a schema to the response.

        :param method: HTTP method to use

        :param path: Path fragment to add to the end of the URL

        :param schema: A schema object which this request must

        :param params: URL parameters to include

        :param timeout: The timeout to pass to requests
        :type timeout: Either a (connect_timeout, read_timeout) 2-tuple or a
            single number that will be used for both the connect timeout and
            the read timeout. The values are in seconds and can be either ints
            or floats. See:
            https://docs.python-requests.org/en/latest/user/quickstart/#timeouts
            https://docs.python-requests.org/en/latest/user/advanced/#timeouts

        :param headers: Headers to include

        :param url_stub: Path prefix

        :raise CanvasAPIError: For any validation or request errors

        :return: The result of applying the schema to the response
        """
        # Always request the maximum items per page for requests which return
        # more than one thing
        if schema.many:
            if params is None:
                params = {}

            params["per_page"] = self.PAGINATION_PER_PAGE

        request = requests.Request(
            method, self._get_url(path, params, url_stub), headers=headers
        ).prepare()

        return self._send_prepared(request, schema, timeout)

    def _get_url(self, path, params, url_stub):
        return f"https://{self._canvas_host}{url_stub}/{path}" + (
            "?" + urlencode(params) if params else ""
        )

    def _send_prepared(self, request, schema, timeout, request_depth=1) -> list:
        response: Response = None  # type:ignore  # noqa: PGH003

        try:
            response = self._session.send(request, timeout=timeout)
            response.raise_for_status()
        except RequestException as err:
            CanvasAPIError.raise_from(err, request, response)

        result: list = None  # type: ignore  # noqa: PGH003
        try:
            result = schema(response).parse()
        except ExternalRequestError as err:
            CanvasAPIError.raise_from(err, request, response, err.validation_errors)

        # Handle pagination links. See:
        # https://canvas.instructure.com/doc/api/file.pagination.html
        next_url = response.links.get("next")
        if next_url:
            # We can only append results if the response is expecting multiple
            # items from the Canvas API
            if not schema.many:
                CanvasAPIError.raise_from(
                    TypeError(
                        "Canvas returned paginated results but we expected a single value"
                    ),
                    request,
                    response,
                )

            # Don't make requests forever
            if request_depth < self.PAGINATION_MAXIMUM_REQUESTS:
                new_request = deepcopy(request)
                new_request.url = next_url["url"]
                result.extend(
                    self._send_prepared(
                        new_request, schema, timeout, request_depth=request_depth + 1
                    )
                )

        return result
