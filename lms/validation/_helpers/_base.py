"""Base classes for validation schemas."""
import marshmallow
from webargs import pyramidparser

from lms.validation._exceptions import ValidationError


__all__ = ["PyramidRequestSchema", "RequestsResponseSchema"]


class _BaseSchema(marshmallow.Schema):
    """Base class for all schemas."""

    class Meta:
        """Marshmallow options for all schemas."""

        # Silence a strict=False deprecation warning from marshmallow.
        # TODO: Remove this once we've upgraded to marshmallow 3.
        strict = True


class PyramidRequestSchema(_BaseSchema):
    """Base class for schemas that validate Pyramid requests."""

    _parser = pyramidparser.PyramidParser()

    def __init__(self, request):
        super().__init__()
        self.context = {"request": request}

    def parse(self, *args, **kwargs):
        """
        Parse and validate the request.

        Use this schema to parse and validate ``self.context["request"]`` and
        either return the successfully parsed params or raise a validation
        error.

        :raise lms.validation.ValidationError: if the request isn't valid
        """
        return self._parser.parse(self, self.context["request"], *args, **kwargs)

    @staticmethod
    @_parser.error_handler
    def _handle_error(error, _req, _schema, _status_code, _headers):
        raise ValidationError(messages=error.messages) from error


class RequestsResponseSchema(_BaseSchema):
    """Base class for schemas that validate ``requests`` lib responses."""

    def __init__(self, response):
        super().__init__()
        self.context = {"response": response}

    def parse(self, *args, **kwargs):
        """
        Parse and validate the response.

        Use this schema to parse and validate ``self.context["response"]`` and
        either return the successfully parsed params or raise a validation
        error.

        :raise lms.validation.ValidationError: if the response isn't valid
        """
        try:
            result = self.load(self.context["response"], *args, **kwargs)
        except marshmallow.ValidationError as err:
            raise ValidationError(messages=err.messages) from err

        return result.data

    @marshmallow.pre_load
    def _pre_load(self, response):  # pylint: disable=no-self-use
        try:
            return response.json()
        except ValueError as err:
            raise marshmallow.ValidationError(
                "response doesn't have a valid JSON body"
            ) from err
