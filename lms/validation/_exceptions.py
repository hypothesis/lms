from urllib.parse import urlencode, urlparse

from pyramid import httpexceptions
# pylint: disable=too-many-ancestors
from pyramid.httpexceptions import HTTPFound

__all__ = [
    "ValidationError",
]


class ValidationError(
    httpexceptions.HTTPUnprocessableEntity
):  # pylint: disable=too-many-ancestors
    """
    A schema validation failure.

    This is the base class for all :mod:`~lms.validation` exception classes.
    """

    def __init__(self, messages):
        """
        Initialise a schema validation exception.

        ``messages`` should be a dict mapping field names to lists of error
        messages for those fields. For example::

            {
                "username": [
                    "username must be at least six characters long.",
                    "username cannot contain '@'.",
                ],
                "email": ['"foo" is not a valid email address.'],
                "_schema": ["OAuth signature verification failed."],
            }

        The special field name ``"_schema"`` indicates error messages that
        don't belong to any one particular field.

        :arg messages: a dict mapping field name strings to lists of error
          messages for the fields
        :type messages: dict[str, list(int)]
        """
        super().__init__()
        self.messages = messages


class LTIToolRedirect(HTTPFound):
    """Something that the user needs to know about in the LTI tool."""

    def __init__(self, location, messages):
        message = self._messages_to_string(messages)
        location = self._update_location(location, message)

        super().__init__(location, message)

    @classmethod
    def _update_location(cls, location, message):
        return (
            urlparse(location)
            ._replace(query=urlencode(dict(location.query, lti_msg=message)))
            .geturl()
        )

    @classmethod
    def _messages_to_string(cls, messages):
        parts = []
        for field, errors in messages.items():
            for error in errors:
                parts.append(f"Field '{field}': {error}")

        return ", ".join(parts)
