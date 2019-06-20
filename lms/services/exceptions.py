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


class ExternalRequestError(ServiceError):
    """
    A problem with a network request to an external service.

    :param response: The response from the HTTP request to the h API
    :type response: requests.Response
    """

    def __init__(self, explanation=None, response=None):
        super().__init__()
        self.explanation = explanation
        self.response = response

    def __str__(self):
        if self.response is None:
            return self.explanation

        # Log the details of the response. This goes to both Sentry and the
        # application's logs. It's helpful for debugging to know how the
        # external service responded.
        parts = [
            str(self.response.status_code or ""),
            self.response.reason,
            self.response.text,
        ]
        return " ".join([part for part in parts if part])


class HAPIError(ExternalRequestError):
    """
    A problem with an h API request.

    Raised whenever an h API request times out or when an unsuccessful, invalid
    or unexpected response is received from the h API.
    """


class HAPINotFoundError(HAPIError):
    """A 404 error from an API request."""


class CanvasAPIError(ExternalRequestError):
    """
    A problem with a Canvas API request.

    Raised whenever a Canvas API request times out or when an unsuccessful,
    invalid or unexpected response is received from the Canvas API.
    """
