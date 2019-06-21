"""Base classes for validation schemas."""
import marshmallow
from webargs import pyramidparser

from lms.validation._exceptions import ValidationError


__all__ = ["PyramidRequestSchema"]


_PYRAMID_PARSER = pyramidparser.PyramidParser()


class _BaseSchema(marshmallow.Schema):
    """Base class for all schemas."""

    class Meta:
        """Marshmallow options for all schemas."""

        # Silence a strict=False deprecation warning from marshmallow.
        # TODO: Remove this once we've upgraded to marshmallow 3.
        strict = True


class PyramidRequestSchema(_BaseSchema):
    """Base class for schemas that validate Pyramid requests."""

    def __init__(self, request):
        super().__init__()

        # Storing context needed for serialization or deserialization in
        # self.context is a marshmallow convention.
        self.context = {"request": request}

    def parse(self, *args, **kwargs):
        """
        Parse and validate the request.

        Use this schema to parse and validate ``self.context["request"]`` and
        either return the successfully parsed params or raise a validation
        error.

        :raise lms.validation.ValidationError: if the request isn't valid
        """
        return _PYRAMID_PARSER.parse(self, self.context["request"], *args, **kwargs)


@_PYRAMID_PARSER.error_handler
def _handle_error(error, _req, _schema, _status_code, _headers):
    raise ValidationError(messages=error.messages) from error
