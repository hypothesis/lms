from lms.models.oauth2_token import Service


class JWTError(Exception):
    """A problem with a JWT."""


class ExpiredJWTError(JWTError):
    """Decoding a JWT failed because the JWT was expired."""


class InvalidJWTError(JWTError):
    """Decoding a JWT failed because the JWT was invalid."""


class ExternalRequestError(Exception):
    """
    A problem with a network request to an external service.

    :arg message: A short error message for displaying to the user
    :type message: str

    :arg refreshable: True if the error can be fixed by refreshing an access token
    :arg refresh_route:
        If `refreshable` is True, the name of the API route that should be
        invoked to perform the token refresh. If `None`, the default route for
        the current LMS is used.
    :arg refresh_service:
        If `refreshable` is True, the API service whose token should be refreshed.
        If `None`, the LMS's main API is assumed.

    :arg request: The request that was sent
    :type request: requests.PreparedRequest

    :arg response: The response that was received
    :type response: requests.Response

    :arg validation_errors: Any errors with validation the response
    :type validation_errors: JSON-serializable dict
    """

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        message=None,
        request=None,
        response=None,
        validation_errors=None,
        refreshable=False,
        refresh_route: str | None = None,
        refresh_service: Service | None = None,
    ):
        super().__init__()
        self.message = message
        self.request = request
        self.response = response
        self.validation_errors = validation_errors
        self.refreshable = refreshable
        self.refresh_route = refresh_route
        self.refresh_service = refresh_service

    @property
    def url(self) -> str | None:
        """Return the request's URL."""
        return getattr(self.request, "url", None)

    @property
    def method(self) -> str | None:
        """Return the HTTP request method."""
        return getattr(self.request, "method", None)

    @property
    def request_body(self) -> str | None:
        """Return the request body."""
        return getattr(self.request, "body", None)

    @property
    def status_code(self) -> int | None:
        """Return the response's status code."""
        return getattr(self.response, "status_code", None)

    @property
    def reason(self) -> str | None:
        """Return the response's HTTP reason string, e.g. 'Bad Request'."""
        return getattr(self.response, "reason", None)

    @property
    def response_body(self) -> str | None:
        """Return the response body."""
        return getattr(self.response, "text", None)

    def __repr__(self) -> str:
        return _repr_external_request_exception(self)

    def __str__(self):
        return repr(self)


class ExternalAsyncRequestError(Exception):
    def __init__(self, response=None):
        super().__init__()
        self.response = response

        # For compatibility with ExternalRequestError.
        self.message = None
        self.request = None
        self.validation_errors = None

    @property
    def _request_info(self):
        return getattr(self.response, "request_info", None) or getattr(
            self.__cause__, "request_info", None
        )

    @property
    def url(self) -> str | None:
        """Return the request's URL."""
        return str(url) if (url := getattr(self._request_info, "url", None)) else None

    @property
    def method(self) -> str | None:
        """Return the HTTP request method."""
        return getattr(self._request_info, "method", None)

    @property
    def status_code(self) -> int | None:
        """Return the response's status code."""
        return getattr(self.response, "status", None)

    @property
    def request_body(self) -> None:
        """Return the request body."""
        return None

    @property
    def reason(self) -> str | None:
        """Return the response's HTTP reason string, e.g. 'Bad Request'."""
        return getattr(self.response, "reason", None)

    @property
    def response_body(self) -> str | None:
        """Return the response body."""
        return getattr(self.response, "sync_text", None)

    def __repr__(self) -> str:
        return _repr_external_request_exception(self)

    def __str__(self):
        return repr(self)


class OAuth2TokenError(ExternalRequestError):
    """
    A problem with an OAuth 2 token for an external API.

    This is raised when we don't have an access token for the current user or
    when our access token doesn't work (e.g. because it's expired or been
    revoked).
    """


class CanvasAPIError(ExternalRequestError):
    """A problem with a Canvas API request."""

    @classmethod
    def raise_from(cls, cause, request, response, validation_errors=None):
        """
        Raise a :exc:`lms.services.CanvasAPIError` from the given ``cause``.

        ``cause`` can be any kind of exception, for example any
        :exc:`requests.RequestException` subclass, or a
        :exc:`lms.validation.ValidationError` (used when a 2xx response was
        received from Canvas, but the response body was invalid).

        If ``cause`` is a :mod:`requests` exception corresponding to a 401
        Unauthorized response from the Canvas API (indicating that the access token
        we used was expired or has been deleted) then
        :exc:`lms.services.OAuth2TokenError` will be raised.

        If ``cause`` indicates any other kind of unsuccessful or invalid response
        from Canvas, or a network error etc, then
        :exc:`lms.services.CanvasAPIServerError` will be raised.

        The given ``cause`` will be set as the raised exception's ``__cause__``
        attribute (standard Python exception chaining).

        The given `request`, `response` and `validation_errors` arguments will
        be set as the `request`, `response` and `validation_errors` attributes
        of the raised exception.
        """
        kwargs = {
            "message": "Calling the Canvas API failed",
            "request": request,
            "response": response,
            "validation_errors": validation_errors,
        }

        if response is None:
            raise CanvasAPIServerError(**kwargs) from cause

        status_code = getattr(response, "status_code", None)

        try:
            response_json = response.json()
        except ValueError:
            raise CanvasAPIServerError(**kwargs) from cause

        if not isinstance(response_json, dict):
            raise CanvasAPIServerError(**kwargs) from cause

        errors = response_json.get("errors", [])

        error_description = response_json.get("error_description", "")

        if {"message": "Invalid access token."} in errors:
            raise OAuth2TokenError(refreshable=True, **kwargs) from cause

        if error_description == "refresh_token not found":
            raise OAuth2TokenError(**kwargs) from cause

        if (
            status_code == 401
            and {"message": "Insufficient scopes on access token."} in errors
        ):
            raise OAuth2TokenError(**kwargs) from cause

        if status_code in (401, 403):
            raise CanvasAPIPermissionError(**kwargs) from cause

        raise CanvasAPIServerError(**kwargs) from cause


class CanvasAPIPermissionError(CanvasAPIError):
    """
    A Canvas API permissions error.

    This happens when the user's access token is fine but they don't have
    permission to carry out the requested action. For example a user might not
    have permission to get a public URL for a file if they don't have
    permission to read that file.
    """

    error_code = "canvas_api_permission_error"


class CanvasAPIServerError(CanvasAPIError):
    """
    A server error during a Canvas API request.

    Raised when a Canvas API request fails in an unexpected way: for example
    the request times out, or we receive an unexpected response.
    """


class SerializableError(Exception):
    """An exception compatible with our default error handling for APIs."""

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        details: dict | None = None,
    ):
        """
        Initialise the error.

        :param message: Message to display to the user (if any)
        :param error_code: Error code to allow client side code to detect
            this error
        :param details: A JSON serializable payload of extra info
        """
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details


class FileNotFoundInCourse(SerializableError):
    """A file wasn't found in the current course."""

    def __init__(self, error_code: str, document_id):
        super().__init__(error_code=error_code, details={"document_id": document_id})


class StudentNotInCourse(SerializableError):
    """A student is no longer in the current course."""

    def __init__(self, grading_id):
        super().__init__(
            error_code="student_not_in_course", details={"grading_id": grading_id}
        )


def _repr_external_request_exception(exception):
    # Include the details of the request and response for debugging. This
    # appears in the logs and in tools like Sentry and Papertrail.
    request = (
        "Request("
        f"method={exception.method!r}, "
        f"url={exception.url!r}, "
        f"body={exception.request_body!r}"
        ")"
    )

    response = (
        "Response("
        f"status_code={exception.status_code!r}, "
        f"reason={exception.reason!r}, "
        f"body={exception.response_body!r}"
        ")"
    )

    # The name of this class or of a subclass if one inherits this method.
    class_name = exception.__class__.__name__

    return (
        f"{class_name}("
        f"message={exception.message!r}, "
        f"request={request}, "
        f"response={response}, "
        f"validation_errors={exception.validation_errors!r})"
    )
