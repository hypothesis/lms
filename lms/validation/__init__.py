"""
Schemas for parsing and validating requests.

This package contains schemas that views can use to validate and parse
requests. The idea is that the request is validated before the view is called.
If validation fails an error response is sent back and the view is never
called. If validation succeeds the parsed and validated parameters are made
available to the view as ``request.parsed_params``. The view's own code can
assume that all the parsed params are valid and that all required params are
present.

Usage::

    from lms.validation import FOO_SCHEMA

    @view_config(..., schema=FOO_SCHEMA)
    def foo_view(request):
        validated_arg_1 = request.parsed_params["validated_arg_1"]
        validated_arg_2 = request.parsed_params["validated_arg_2"]
        ...

Note that we're using our own view deriver (the ``schema`` argument to
``view_config``) to integrate our schemas and views, rather than using webargs's
``@use_args()`` / ``@use_kwargs()`` decorators. For the reasons for this see
commit message f61a5ff3cae6b983e24db809d8e4b4933aca1e92.
"""
from webargs import pyramidparser

from lms.validation._exceptions import (
    ValidationError,
    ExpiredSessionTokenError,
    MissingSessionTokenError,
    InvalidSessionTokenError,
    MissingStateParamError,
    ExpiredStateParamError,
    InvalidStateParamError,
)
from lms.validation._oauth import CanvasOAuthCallbackSchema
from lms.validation._launch_params import LaunchParamsSchema
from lms.validation._bearer_token import BearerTokenSchema
from lms.validation._module_item_configuration import ConfigureModuleItemSchema
from lms.validation._helpers import instantiate_schema


__all__ = (
    "parser",
    "CanvasOAuthCallbackSchema",
    "BearerTokenSchema",
    "LaunchParamsSchema",
    "ConfigureModuleItemSchema",
    "ValidationError",
    "ExpiredSessionTokenError",
    "MissingSessionTokenError",
    "InvalidSessionTokenError",
    "MissingStateParamError",
    "InvalidStateParamError",
    "ExpiredStateParamError",
)


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

    This is a Pyramid "view deriver" that a view can activate by having a
    ``schema=some_schema`` argument in its view config. For example
    ``@view_config(..., schema=lms.validation.foo_schema)``. See:

    https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#custom-view-derivers
    """
    if "schema" in info.options:

        def wrapper_view(context, request):
            # Use the view's configured schema to validate the request,
            # and make the validated and parsed request params available as
            # request.parsed_params.
            request.parsed_params = parser.parse(
                instantiate_schema(info.options["schema"], request), request
            )

            # Call the view normally.
            return view(context, request)

        return wrapper_view
    return view


def includeme(config):
    _validated_view.options = ["schema"]
    config.add_view_deriver(_validated_view)
