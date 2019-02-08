from webargs import pyramidparser

from lms.validation._exceptions import ValidationError
from lms.validation._oauth import CANVAS_OAUTH_CALLBACK_SCHEMA


__all__ = ("parser", "CANVAS_OAUTH_CALLBACK_SCHEMA", "ValidationError")


parser = pyramidparser.PyramidParser()


@parser.error_handler
def _handle_error(error, _req, _schema, _status_code, _headers):
    raise ValidationError(messages=error.messages) from error


def _validated_view(view, info):
    """
    Validate the request and then call the view.

    Validate the request params using the view's configured
    schema and, if validation succeeds, go on to call the view normally.

    Make the validated and parsed params available to the view as
    ``request.parsed_params``.

    If validation fails don't call the view.

    This is a Pyramid "view deriver" that Pyramid calls if the view has a
    ``schema=some_schema`` argument in its view config. For example
    ``@view_config(..., schema=lms.validation.foo_schema)``. See:

    https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#custom-view-derivers
    """
    if "schema" in info.options:

        def wrapper_view(context, request):
            # Use the view's configured schema to validate the request,
            # and make the validated and parsed request params available as
            # request.parsed_params.
            # If validation fails this will raise ValidationError and the view won't be called.
            request.parsed_params = parser.parse(info.options["schema"], request)

            # Call the view normally.
            return view(context, request)

        return wrapper_view
    return view


def includeme(config):
    _validated_view.options = ["schema"]
    config.add_view_deriver(_validated_view)
