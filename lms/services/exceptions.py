from pyramid.httpexceptions import HTTPInternalServerError


class ServiceError(Exception):
    """Base class for all :mod:`lms.services` exceptions."""


class ConsumerKeyError(ServiceError):
    """Raised when a given ``consumer_key`` doesn't exist in the DB."""


class HAPIError(HTTPInternalServerError):  # pylint: disable=too-many-ancestors
    """
    A problem with an h API request.

    This exception class is raised whenever an h API request times out or when
    an unsuccessful, invalid or unexpected response is received from the h API.

    An HAPIError is a 500 Internal Server Error response (HTTPInternalServerError
    subclass) rather than, say, a 502 Bad Gateway because Cloudflare intercepts
    gateway error responses and replaces our error page with its own error
    page, and we don't want that.

    Any arguments or keyword arguments other than ``response`` are passed
    through to HTTPInternalServerError.

    :param response: The response from the HTTP request to the h API
    :type response: requests.Response
    """

    def __init__(self, *args, response=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.response = response

    def __str__(self):
        if self.response is None:
            return super().__str__()

        # Log the details of the h API response. This goes to both Sentry and
        # the application's logs. It's helpful for debugging to know how h
        # responded.
        parts = [
            str(self.response.status_code or ""),
            self.response.reason,
            self.response.text,
        ]
        return " ".join([part for part in parts if part])


class HAPINotFoundError(HAPIError):  # pylint: disable=too-many-ancestors
    """A 404 error from an API request."""
