"""Base classes for validation schemas."""
import marshmallow
from webargs import pyramidparser

from lms.validation._exceptions import ValidationError


__all__ = ["PyramidRequestSchema", "RequestsResponseSchema"]


class _BaseSchema(marshmallow.Schema):
    """Base class for all schemas."""

    many = None
    """
    Whether or not this schema validates collections of objects by default.

    If this is ``None`` then marshmallow's default behavior will be used -- the
    schema will expect to validate a single object rather than a collection of
    similar objects.

    To validate a collection of objects where each object is expected to have
    the same fields, create a schema whose fields are the fields that each
    object is expected to have and set ``many = True``:

        class MySchema(_BaseSchema):
            many = True

            field_1 = fields.Str(...)
            field_2 = fields.Integer(...)
            field_3 = fields.String(...)

    For more documentation on validating lists of objects see:

        https://marshmallow.readthedocs.io/en/2.x-line/quickstart.html#handling-collections-of-objects
    """

    def __init__(self):
        super().__init__(many=self.many)

    class Meta:
        """Marshmallow options for all schemas."""

        # Silence a strict=False deprecation warning from marshmallow.
        # TODO: Remove this once we've upgraded to marshmallow 3.
        strict = True


class PyramidRequestSchema(_BaseSchema):
    """Base class for schemas that validate Pyramid requests."""

    locations = None
    """
    The locations where webargs should look for the parameters.

    If this is ``None`` then webargs's default locations will be used.

    Subclasses can override this to control where parameters are searched for::

        class MySchema(PyramidRequestSchema):
            locations = ["form"]

            ...

    For the list of available locations see:
    https://webargs.readthedocs.io/en/latest/quickstart.html#request-locations
    """

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
        kwargs.setdefault("locations", self.locations)
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

    @marshmallow.pre_load(pass_many=True)
    def _pre_load(self, response, _many):  # pylint: disable=no-self-use
        try:
            return response.json()
        except ValueError as err:
            raise marshmallow.ValidationError(
                "response doesn't have a valid JSON body"
            ) from err
