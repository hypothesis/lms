from lms.validation._exceptions import ValidationError

# pylint: disable=too-many-ancestors
# ValidationError has a large hierarchy, but we need to inherit from it

__all__ = [
    "ExpiredSessionTokenError",
    "MissingSessionTokenError",
    "InvalidSessionTokenError",
    "MissingStateParamError",
    "ExpiredStateParamError",
    "InvalidStateParamError",
]


class ExpiredSessionTokenError(ValidationError):
    """Raised when the request has an expired session token."""


class MissingSessionTokenError(ValidationError):
    """Raised when the request has no session token."""


class InvalidSessionTokenError(ValidationError):
    """Raised when the request has an invalid session token."""


class MissingStateParamError(ValidationError):
    """An OAuth 2 redirect request was missing the ``state`` param."""

    def __init__(self):
        super().__init__({"state": ["Missing `state` parameter"]})


class ExpiredStateParamError(ValidationError):
    """An OAuth 2 redirect request had an expired ``state`` param."""

    def __init__(self):
        super().__init__({"state": ["Expired `state` parameter"]})


class InvalidStateParamError(ValidationError):
    """An OAuth 2 redirect request had an invalid ``state`` param."""

    def __init__(self):
        super().__init__({"state": ["Invalid `state` parameter"]})
