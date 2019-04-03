from pyramid import httpexceptions


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
