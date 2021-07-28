class ServiceError(Exception):
    """Base class for all :mod:`lms.services` exceptions."""


class LTILaunchVerificationError(ServiceError):
    """
    Raised when LTI launch request verification fails.

    This is the base class for all LTI launch request verification errors.
    Different subclasses of this exception class are raised for specific
    failure types.
    """


class ConsumerKeyError(LTILaunchVerificationError):
    """Raised when a given ``consumer_key`` doesn't exist in the DB."""


class LTIOAuthError(LTILaunchVerificationError):
    """Raised when OAuth signature verification of a launch request fails."""


class ExternalRequestError(ServiceError):
    """
    A problem with a network request to an external service.

    :arg explanation: A short error message for displaying to the user
    :type explanation: str

    :arg response: The external service's response to our HTTP request, if any
    :type response: requests.Response or ``None``

    :arg details: Additional details about what went wrong, for debugging
    :type details: JSON-serializable dict or ``None``
    """

    def __init__(self, explanation=None, response=None, details=None):
        super().__init__()
        self.explanation = explanation
        self.response = response
        self.details = details

    def __str__(self):
        if self.response is None:
            return self.explanation

        # Log the details of the response. This goes to both Sentry and the
        # application's logs. It's helpful for debugging to know how the
        # external service responded.
        parts = [
            self.explanation + ":",
            str(self.response.status_code or ""),
            self.response.reason,
            self.response.text,
        ]
        return " ".join([part for part in parts if part])


class OAuth2TokenError(ExternalRequestError):
    """
    A problem with an OAuth 2 token for an external API.

    This is raised when we don't have an access token for the current user or
    when our access token doesn't work (e.g. because it's expired or been
    revoked).
    """


class HAPIError(ExternalRequestError):
    """
    A problem with an h API request.

    Raised whenever an h API request times out or when an unsuccessful, invalid
    or unexpected response is received from the h API.
    """


class ProxyAPIError(ExternalRequestError):
    """
    A problem with a third-party API request.

    Raised whenever a third-party API request times out or when an
    unsuccessful, invalid or unexpected response is received from a third-party
    API.
    """


class CanvasAPIError(ProxyAPIError):
    """A problem with a Canvas API request."""

    @classmethod
    def raise_from(cls, cause):
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

        If ``cause`` has a ``response`` attribute then it will be set as the
        ``response`` attribute of the raised exception. Otherwise
        ``<raised_exception>.response`` will be ``None``.
        """
        response = getattr(cause, "response", None)

        exception_class = cls._exception_class(response)

        details = {
            "validation_errors": getattr(cause, "messages", None),
        }

        if response is None:
            details["response"] = None
        else:
            details["response"] = {
                "status": f"{response.status_code} {response.reason}"
            }
            details["response"]["body"] = response.text[:150]
            if len(response.text) > 150:
                details["response"]["body"] += "..."

        raise exception_class(
            explanation="Calling the Canvas API failed",
            response=response,
            details=details,
        ) from cause

    @staticmethod
    def _exception_class(response):
        """Return the exception class to raise for the given response."""
        if response is None:
            return CanvasAPIServerError

        status_code = getattr(response, "status_code", None)

        try:
            response_json = response.json()
        except ValueError:
            response_json = {}

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


class LTIOutcomesAPIError(ExternalRequestError):
    """
    A problem with a request to an LTI Outcomes-compliant API.

    Raised whenever an LTI outcomes API request times out or when an
    unsuccessful, invalid or unexpected response is received from the API.
    """


class CanvasFileNotFoundInCourse(ServiceError):
    """A Canvas file ID wasn't found in the current course."""

    error_code = "canvas_file_not_found_in_course"

    def __init__(self, file_id):
        self.details = {"file_id": file_id}
        super().__init__(self.details)


class HTTPError(ServiceError):
    """A problem with an HTTP request to an external service."""

    def __init__(self, response=None):
        super().__init__(response)
        self.response = response


class BlackboardFileNotFoundInCourse(ServiceError):
    """A Blackboard file ID wasn't found in the current course."""

    error_code = "blackboard_file_not_found_in_course"

    def __init__(self, file_id):
        self.details = {"file_id": file_id}
        super().__init__(self.details)
