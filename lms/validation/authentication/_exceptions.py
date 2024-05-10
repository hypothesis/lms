from lms.validation._exceptions import ValidationError

# ValidationError has a large hierarchy, but we need to inherit from it

__all__ = [
    "MissingStateParamError",
    "ExpiredStateParamError",
    "InvalidStateParamError",
]


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
