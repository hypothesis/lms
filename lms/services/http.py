import requests
from requests import RequestException

from lms.services.exceptions import HTTPError


class HTTPService:
    """Send HTTP requests with `requests` and receive the responses."""

    def __init__(self, _session=None):
        # A requests session is used so that cookies are persisted across
        # requests and urllib3 connection pooling is used (which means that
        # underlying TCP connections are re-used when making multiple requests
        # to the same host, e.g. pagination).
        #
        # See https://docs.python-requests.org/en/latest/user/advanced/#session-objects
        self._session = _session or requests.Session()

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

    def request(self, method, url, timeout=(10, 10), **kwargs):
        """
        Send a request with `requests` and return the requests.Response object.

        :param method: The HTTP method to use, one of "GET", "PUT", "POST",
            "PATCH", "DELETE", "OPTIONS" or "HEAD"

        :param url: The URL to request

        :param timeout: How long (in seconds) to wait before raising an error.

            This can be a (connect_timeout, read_timeout) 2-tuple or it can be
            a single float that will be used as both the connect and read
            timeout.

            Good practice is to set this to slightly larger than a multiple of
            3, which is the default TCP packet retransmission window. See:
            https://docs.python-requests.org/en/master/user/advanced/#timeouts

            Note that the read_timeout is *not* a time limit on the entire
            response download. It's a time limit on how long to wait *between
            bytes from the server*. The entire download can take much longer.

        :param kwargs: Any other keyword arguments will be passed directly to
            requests.Session().request():
            https://docs.python-requests.org/en/latest/api/#requests.Session.request

        :raise HTTPError: If sending the request or receiving the response
            fails (DNS failure, refused connection, timeout, too many
            redirects, etc).

            The original exception from requests will be available as
            HTTPError.__cause__.

            In this case HTTPError.response will be None.

        :raise HTTPError: If an error response (4xx or 5xx) is received.

            The original exception from requests will be available as
            HTTPError.__cause__.

            The error response will be available as HTTPError.response.
        """
        response = None

        try:
            response = self._session.request(
                method,
                url,
                timeout=timeout,
                **kwargs,
            )
            response.raise_for_status()
        except RequestException as err:
            raise HTTPError(response) from err

        return response


def factory(_context, _request):
    return HTTPService()
