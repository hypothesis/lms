import requests
from requests import RequestException

from lms.services.exceptions import HTTPError, HTTPValidationError
from lms.validation import ValidationError


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

    def request(
        self,
        method,
        url,
        params=None,
        data=None,
        json=None,
        headers=None,
        auth=None,
        timeout=(10, 10),
        schema=None,
        **kwargs,
    ):  # pylint:disable=too-many-arguments
        """
        Send a request with `requests` and return the requests.Response object.

        Also supports validating the response with a `marshmallow` schema. If a
        `schema` argument is given the response will be validated using the
        schema and the schema output will be added to the returned response as
        response.validated_data.

        The schema must be a RequestsResponseSchema sub-class.

        HTTPValidationError will be raised if schema validation fails.

        :param method: The HTTP method to use, one of "GET", "PUT", "POST",
            "PATCH", "DELETE", "OPTIONS" or "HEAD"

        :param url: The URL to request

        :param params: Query params to append to the URL.

            This can be a dict or list of tuples and it'll be serialized into a
            query string.

            Or it can be a byte string and it'll be used directly as the query
            string.

        :param data: Form data to send in the body of the request.

            This can be a dict or list of tuples and it'll be serialized into a
            form body.

            Or it can be bytes or a file-like object (e.g. a JSON byte string)
            it'll be used directly as the request body.

        :param json: Data to send in the body of the request as JSON.

            Using this changes the request's content-type to application/json.

            This can't be used at the same time as the `data` argument.

        :type json: Any JSON-serializable object (e.g. a list or dict)

        :param headers: Headers to send in the request.

            Header values should be byte strings not unicode.

        :type headers: dict

        :param auth: Authorization to send in the request's Authorization header.

            This can be a (user, pass) 2-tuple which will be serialized using
            HTTP Basic Authentication.

            Or it can be a callable in order to implement other authentication
            schemes. `requests` itself and libraries like `requests_oauthlib`
            provide auth callables that you can use or you can write your own.

            See: https://docs.python-requests.org/en/master/user/authentication/

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

        :param schema: A schema class to use to validate the response
        :type schema: lms.validation.RequestsResponseSchema

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

        :raise HTTPValidationError: If a `schema` argument is given and the
            response fails validation with the schema.

            The original lms.validation.ValidationError will be available as
            HTTPValidationError.__cause__.

            The invalid response will be available as
            HTTPValidationError.response.
        """
        response = None

        try:
            response = self._session.request(
                method,
                url,
                params=params,
                data=data,
                json=json,
                headers=headers,
                auth=auth,
                timeout=timeout,
                **kwargs,
            )
            response.raise_for_status()
        except RequestException as err:
            raise HTTPError(response) from err

        if schema:
            try:
                response.validated_data = schema(response).parse()
            except ValidationError as err:
                raise HTTPValidationError(response) from err

        return response


def factory(_context, _request):
    return HTTPService()
