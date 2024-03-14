from requests import RequestException, Response, Session

from lms.services.exceptions import ExternalRequestError


class HTTPService:
    """Send HTTP requests with `requests` and receive the responses."""

    # This is here mostly to let auto-spec know about it in the tests
    session: Session = None  # typing: ignore
    """The underlying requests Session."""

    def __init__(self):
        # A session is used so that cookies are persisted across
        # requests and urllib3 connection pooling is used (which means that
        # underlying TCP connections are re-used when making multiple requests
        # to the same host, e.g. pagination).

        # See https://docs.python-requests.org/en/latest/user/advanced/#session-objects
        self.session = Session()

    def request(self, method, url, timeout=(10, 10), **kwargs) -> Response:
        """
        Send a request with `requests` and return the response object.

        This method accepts the same arguments as `requests.Session.request`
        with the same meaning which can be seen here:

        https://requests.readthedocs.io/en/latest/api/#requests.Session.request

        :raises ExternalRequestError: For any request based failure or if the
            response is an error (4xx or 5xx response).
        """
        response = None

        try:
            response = self.session.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
        except RequestException as err:
            raise ExternalRequestError(request=err.request, response=response) from err

        return response

    def get(self, *args, **kwargs):
        return self.request("GET", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request("PUT", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request("POST", *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request("PATCH", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request("DELETE", *args, **kwargs)


def factory(_context, _request):
    return HTTPService()
