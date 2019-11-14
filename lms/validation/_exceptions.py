from urllib.parse import parse_qs, urlencode, urlparse

from pyramid import httpexceptions
from pyramid.httpexceptions import HTTPFound

# pylint: disable=too-many-ancestors

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
    """An LTI validation error that should be returned to the tool consumer."""

    def __init__(self, location, messages):
        """
        Create an exception with redirect information for an LTI tool.

        :param location: The URL to redirect to
        :param messages: A dict of lists of validation messages where the keys
                         are fields and the values are lists of descriptions of
                         problems
        :raises ValueError: If messages is malformed
        """
        message = self._messages_to_string(messages)

        super().__init__(
            location=self._add_lti_message_to_url(location, message), detail=message
        )

    @classmethod
    def _add_lti_message_to_url(cls, location, message):
        location = urlparse(location)
        query = parse_qs(location.query)
        query["lti_msg"] = message
        query = urlencode(query, doseq=True)

        return location._replace(query=query).geturl()

    @classmethod
    def _messages_to_string(cls, messages):
        if not isinstance(messages, dict):
            raise ValueError("Messages must be a dict of lists: field -> [errors]")

        parts = []
        for field, errors in messages.items():
            if not isinstance(errors, list):
                raise ValueError("Messages must be a dict of lists: field -> [errors]")

            for error in errors:
                parts.append(f"Field '{field}': {error}")

        return ", ".join(parts)
