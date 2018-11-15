from pyramid.httpexceptions import HTTPInternalServerError


class HAPIError(HTTPInternalServerError):  # pylint: disable=too-many-ancestors
    """
    A problem with an h API request.

    This exception class is raised whenever an h API request times out or when
    an unsuccessful, invalid or unexpected response is received from the h API.

    An HAPIError is a 500 Internal Server Error response (HTTPInternalServerError
    subclass) rather than, say, a 502 Bad Gateway because Cloudflare intercepts
    gateway error responses and replaces our error page with its own error
    page, and we don't want that.
    """
