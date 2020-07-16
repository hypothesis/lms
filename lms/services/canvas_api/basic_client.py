from copy import deepcopy
from urllib.parse import urlencode

import requests
from requests import RequestException, Session

from lms.services import CanvasAPIError
from lms.validation import ValidationError


class BasicClient:
    PAGINATION_PER_PAGE = 1000
    """The number of items to request at one time.

     This only applies for calls which return more than one, and is subject
     to a secret internal limit applied by Canvas (might be 100?)."""

    PAGINATION_MAXIMUM_REQUESTS = 25
    """The maximum number of calls to make before giving up."""

    def __init__(self, canvas_host):
        self._session = Session()
        self._canvas_host = canvas_host

    def make_request(self, method, path, schema, params=None):
        # Always request the maximum items per page for requests which return
        # more than one thing
        if schema.many:
            if params is None:
                params = {}

            params["per_page"] = self.PAGINATION_PER_PAGE

        return requests.Request(method, self.get_url(path, params)).prepare()

    def get_url(self, path, params=None, url_stub="/_api/v1"):
        return f"https://{self._canvas_host}{url_stub}/{path}" + (
            "?" + urlencode(params) if params else ""
        )

    def send_and_validate(self, request, schema, request_depth=1):
        """
        Send a Canvas API request and validate and return the response.

        If a validation schema is given then the parsed and validated response
        params will be available on the returned response object as
        `response.parsed_params` (a dict).

        :param request: a prepared request to some Canvas API endpoint
        :param schema: The schema class to validate the contents of the response
            with.
        :param request_depth: The number of requests made so far for pagination
        """

        try:
            response = self._session.send(request, timeout=9)
            response.raise_for_status()
        except RequestException as err:
            CanvasAPIError.raise_from(err)

        result = None
        try:
            result = schema(response).parse()
        except ValidationError as err:
            CanvasAPIError.raise_from(err)

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
                    )
                )

            # Don't make requests forever
            if request_depth < self.PAGINATION_MAXIMUM_REQUESTS:
                new_request = deepcopy(request)
                new_request.url = next_url["url"]
                result.extend(
                    self.send_and_validate(
                        new_request, schema, request_depth=request_depth + 1
                    )
                )

        return result
