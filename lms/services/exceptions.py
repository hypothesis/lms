from pyramid.httpexceptions import HTTPInternalServerError


class ServiceError(Exception):
    """Base class for all :mod:`lms.services` exceptions."""


class LTILaunchVerificationError(ServiceError):
    """
    Raised when LTI launch request verification fails.

    This is the base class for all LTI launch request verification errors.
    Different subclasses of this exception class are raised for specific
    failure types.
    """


class NoConsumerKey(LTILaunchVerificationError):
    """Raised when a launch request has no ``oauth_consumer_key`` parameter."""


class ConsumerKeyError(LTILaunchVerificationError):
    """Raised when a given ``consumer_key`` doesn't exist in the DB."""


class LTIOAuthError(LTILaunchVerificationError):
    """Raised when OAuth signature verification of a launch request fails."""


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


class CanvasAPIError(HTTPInternalServerError):  # pylint: disable=too-many-ancestors
    """
    A problem with a Canvas API request.

    This exception class is raised whenever a Canvas API request times out or
    when an unsuccessful, invalid or unexpected response is received from the
    Canvas API.

    An CanvasAPIError is a 500 Internal Server Error response
    (HTTPInternalServerError subclass) rather than, say, a 502 Bad Gateway
    because Cloudflare intercepts gateway error responses and replaces our
    error page with its own error page, and we don't want that.

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

        # Log the details of the Canvas API response. This goes to both Sentry
        # and the application's logs. It's helpful for debugging to know how
        # Canvas responded.
        parts = [
            str(self.response.status_code or ""),
            self.response.reason,
            self.response.text,
        ]
        return " ".join([part for part in parts if part])
