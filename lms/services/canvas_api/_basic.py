"""Low level access to the Canvas API."""

from copy import deepcopy
from urllib.parse import urlencode

import requests
from requests import RequestException, Session

from lms.services import CanvasAPIError
from lms.validation import ValidationError


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

    def send(
        # pylint: disable=too-many-arguments
        self,
        method,
        path,
        schema,
        params=None,
        headers=None,
        url_stub="/api/v1",
    ):
        """
        Make a request to the Canvas API and apply a schema to the response.

        :param method: HTTP method to use
        :param path: Path fragment to add to the end of the URL
        :param schema: A schema object which this request must
        :param params: URL parameters to include
        :param headers: Headers to include
        :param url_stub: Path prefix
        :return: The result of applying the schema to the response
        :raise CanvasAPIError: For any validation or request errors
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

        return self._send_prepared(request, schema)

    def _get_url(self, path, params, url_stub):
        return f"https://{self._canvas_host}{url_stub}/{path}" + (
            "?" + urlencode(params) if params else ""
        )

    def _send_prepared(self, request, schema, request_depth=1):
        try:
            response = self._session.send(request, timeout=9)
            response.raise_for_status()
        except RequestException as err:
            CanvasAPIError.raise_from(err, request, response)

        result = None
        try:
            result = schema(response).parse()
        except ValidationError as err:
            CanvasAPIError.raise_from(err, request, response)

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
                        new_request, schema, request_depth=request_depth + 1
                    )
                )

        return result
