"""Exceptions raised by LTI launch code."""

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.i18n import TranslationString


class LTILaunchError(HTTPBadRequest):  # pylint: disable=too-many-ancestors
    """Base exception for problems handling LTI launches."""

    def __init__(self, message):
        """Initialize the exception with a message."""
        super(LTILaunchError, self).__init__(message)


class MissingLTILaunchParamError(LTILaunchError):  # pylint: disable=too-many-ancestors
    """Exception raised if params required for LTI launch are missing."""

    def __init__(self, data_param):
        """Construct error message with the data param information."""
        message = (
            TranslationString("Required data param for LTI launch missing: ")
            + data_param
        )
        super(MissingLTILaunchParamError, self).__init__(message)
