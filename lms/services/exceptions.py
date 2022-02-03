from typing import Optional


class ExternalRequestError(Exception):
    """
    A problem with a network request to an external service.

    :arg message: A short error message for displaying to the user
    :type message: str

    :arg request: The request that was sent
    :type request: requests.PreparedRequest

    :arg response: The response that was received
    :type response: requests.Response

    :arg validation_errors: Any errors with validation the response
    :type validation_errors: JSON-serializable dict
    """

    def __init__(
        self, message=None, request=None, response=None, validation_errors=None
    ):
        super().__init__()
        self.message = message
        self.request = request
        self.response = response
        self.validation_errors = validation_errors

    @property
    def url(self) -> Optional[str]:
        """Return the request's URL."""
        return getattr(self.request, "url", None)

    @property
    def method(self) -> Optional[str]:
        """Return the HTTP request method."""
        return getattr(self.request, "method", None)

    @property
    def request_body(self) -> Optional[str]:
        """Return the request body."""
        return getattr(self.request, "body", None)

    @property
    def status_code(self) -> Optional[int]:
        """Return the response's status code."""
        return getattr(self.response, "status_code", None)

    @property
    def reason(self) -> Optional[str]:
        """Return the response's HTTP reason string, e.g. 'Bad Request'."""
        return getattr(self.response, "reason", None)

    @property
    def response_body(self) -> Optional[str]:
        """Return the response body."""
        return getattr(self.response, "text", None)

    def __repr__(self) -> str:
        # Include the details of the request and response for debugging. This
        # appears in the logs and in tools like Sentry and Papertrail.
        request = (
            "Request("
            f"method={self.method!r}, "
            f"url={self.url!r}, "
            f"body={self.request_body!r}"
            ")"
        )

        response = (
            "Response("
            f"status_code={self.status_code!r}, "
            f"reason={self.reason!r}, "
            f"body={self.response_body!r}"
            ")"
        )

        # The name of this class or of a subclass if one inherits this method.
        class_name = self.__class__.__name__

        return (
            f"{class_name}("
            f"message={self.message!r}, "
            f"cause={self.__cause__!r}, "
            f"request={request}, "
            f"response={response}, "
            f"validation_errors={self.validation_errors!r})"
        )

    def __str__(self):
        return repr(self)


class ExternalAsyncRequestError(Exception):
    def __init__(
        self, message=None, request=None, response=None, validation_errors=None
    ):
        super().__init__()
        self.message = message
        self.request = request
        self.response = response
        self.validation_errors = validation_errors

    @property
    def _request_info(self):
        return getattr(self.response, "request_info", None) or getattr(
            self.__cause__, "request_info", None
        )

    @property
    def url(self) -> Optional[str]:
        """Return the request's URL."""
        return str(url) if (url := getattr(self._request_info, "url", None)) else None

    @property
    def method(self) -> Optional[str]:
        """Return the HTTP request method."""
        return getattr(self._request_info, "method", None)

    @property
    def status_code(self) -> Optional[int]:
        """Return the response's status code."""
        return getattr(self.response, "status", None)

    @property
    def request_body(self) -> None:
        """Return the request body."""
        return None

    @property
    def reason(self) -> Optional[str]:
        """Return the response's HTTP reason string, e.g. 'Bad Request'."""
        return getattr(self.response, "reason", None)

    @property
    def response_body(self) -> None:
        """Return the response body."""
        return None

    def __repr__(self) -> str:
        # Include the details of the request and response for debugging. This
        # appears in the logs and in tools like Sentry and Papertrail.
        request = (
            "Request("
            f"method={self.method!r}, "
            f"url={self.url!r}, "
            f"body={self.request_body!r}"
            ")"
        )

        response = (
            "Response("
            f"status_code={self.status_code!r}, "
            f"reason={self.reason!r}, "
            f"body={self.response_body!r}"
            ")"
        )

        # The name of this class or of a subclass if one inherits this method.
        class_name = self.__class__.__name__

        return (
            f"{class_name}("
            f"message={self.message!r}, "
            f"cause={self.__cause__!r}, "
            f"request={request}, "
            f"response={response}, "
            f"validation_errors={self.validation_errors!r})"
        )

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
        exception_class = cls._exception_class(response)

        raise exception_class(
            message="Calling the Canvas API failed",
            request=request,
            response=response,
            validation_errors=validation_errors,
        ) from cause

    @staticmethod
    def _exception_class(response):  # pylint:disable=too-many-return-statements
        """Return the exception class to raise for the given response."""
        if response is None:
            return CanvasAPIServerError

        status_code = getattr(response, "status_code", None)

        try:
            response_json = response.json()
        except ValueError:
            return CanvasAPIServerError

        if not isinstance(response_json, dict):
            return CanvasAPIServerError

        errors = response_json.get("errors", [])

        error_description = response_json.get("error_description", "")

        if {"message": "Invalid access token."} in errors:
            return OAuth2TokenError

        if error_description == "refresh_token not found":
            return OAuth2TokenError

        if (
            status_code == 401
            and {"message": "Insufficient scopes on access token."} in errors
        ):
            return OAuth2TokenError

        if status_code == 401:
            return CanvasAPIPermissionError

        return CanvasAPIServerError


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


class CanvasFileNotFoundInCourse(Exception):
    """A Canvas file ID wasn't found in the current course."""

    error_code = "canvas_file_not_found_in_course"

    def __init__(self, file_id):
        self.details = {"file_id": file_id}
        super().__init__(self.details)


class BlackboardFileNotFoundInCourse(Exception):
    """A Blackboard file ID wasn't found in the current course."""

    error_code = "blackboard_file_not_found_in_course"

    def __init__(self, file_id):
        self.details = {"file_id": file_id}
        super().__init__(self.details)
