"""Base classes for validation schemas."""

import marshmallow
from marshmallow import pre_load
from pyramid.httpexceptions import HTTPUnsupportedMediaType
from webargs import pyramidparser

from lms.services.exceptions import ExternalRequestError
from lms.validation._exceptions import ValidationError


class PlainSchema(marshmallow.Schema):
    """Base class for all schemas."""

    many: bool = False
    """
    Whether or not this schema validates collections of objects by default.

    If this is ``False`` then marshmallow's default behavior will be used -- the
    schema will expect to validate a single object rather than a collection of
    similar objects.

    To validate a collection of objects where each object is expected to have
    the same fields, create a schema whose fields are the fields that each
    object is expected to have and set ``many = True``:

        class MySchema(PlainSchema):
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

        # Drop unknown keys, instead of raising an error.
        unknown = marshmallow.EXCLUDE


class PyramidRequestSchema(PlainSchema):
    """Base class for schemas that validate Pyramid requests."""

    location: str | None = None
    """
    The location where webargs should look for the parameters.

    If this is ``None`` then webargs's default location will be used.

    Subclasses can override this to control where parameters are searched for::

        class MySchema(PyramidRequestSchema):
            location = "form"

            ...

    For the list of available locations see:
    https://webargs.readthedocs.io/en/latest/quickstart.html#request-locations
    """

    def __init__(self, request):
        super().__init__()
        self._request = request

    def parse(self, *args, **kwargs):
        """
        Parse and validate the request.

        Use this schema to parse and validate ``self._request`` and
        either return the successfully parsed params or raise a validation
        error.

        :raise lms.validation.ValidationError: if the request isn't valid
        """
        parser = pyramidparser.PyramidParser(
            location=kwargs.pop("location", self.location),
            error_handler=self._handle_error,
            # Disable webargs's DEFAULT_UNKNOWN_BY_LOCATION feature and fall
            # back to the Marshmallow schema's Meta.unknown instead.
            # See https://webargs.readthedocs.io/en/latest/advanced.html#setting-unknown
            unknown=None,
        )
        return parser.parse(self, self._request, *args, **kwargs)

    @staticmethod
    def _handle_error(error, _req, _schema, *, error_status_code, error_headers):  # noqa: ARG004
        raise ValidationError(messages=error.messages) from error


class JSONPyramidRequestSchema(PyramidRequestSchema):
    """A schema which expects JSON content only in a Pyramid request."""

    def __init__(self, request):
        super().__init__(request)

        self.location = "json"

    @pre_load
    def check_content_type(self, data, **_):
        """
        Check the request has content type 'application/json'.

        :raise HTTPUnsupportedMediaType: If the content type is wrong
        """
        content_type = self._request.content_type

        if content_type != "application/json":
            raise HTTPUnsupportedMediaType(  # noqa: TRY003
                f"Unexpected content type. Expected 'application/json' but found '{content_type}'",  # noqa: EM102
            )

        return data


class RequestsResponseSchema(PlainSchema):
    """Base class for schemas that validate ``requests`` lib responses."""

    def __init__(self, response):
        super().__init__()
        self._response = response

    def parse(self, *args, **kwargs):
        """
        Parse and validate the response.

        Use this schema to parse and validate ``self._response`` and
        either return the successfully parsed params or raise a validation
        error.

        :raise ExternalRequestError: if the response isn't valid
        """
        try:
            return self.load(self._response, *args, **kwargs)
        except marshmallow.ValidationError as err:
            request = self._response.request if self._response is not None else None
            validation_errors = err.messages

            raise ExternalRequestError(
                request=request,
                response=self._response,
                validation_errors=validation_errors,
            ) from err

    @marshmallow.pre_load(pass_many=True)
    def _pre_load(self, response, **_kwargs):
        try:
            return response.json()
        except (AttributeError, ValueError) as err:
            raise marshmallow.ValidationError(  # noqa: TRY003
                "response doesn't have a valid JSON body"  # noqa: EM101
            ) from err


@pyramidparser.parser.location_loader("query_and_form")
def _query_and_form(request, _schema):
    """Location for PyramidParser that allows access to both querystring and form data."""
    return request.params
