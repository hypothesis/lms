"""
Schemas for parsing and validating things.

This package contains schemas for parsing and validating things like Pyramid
requests, or :mod:`requests`-library responses.

Validating Pyramid Requests
---------------------------

When validating Pyramid requests the idea is that the request is validated
before the view is called.  If validation fails an error response is sent back
and the view is never called. If validation succeeds the parsed and validated
parameters are made available to the view as ``request.parsed_params``. The
view's own code can assume that all the parsed params are valid and that all
required params are present. Example::

    from lms.validation import FooSchema

    @view_config(..., schema=FooSchema)
    def foo_view(request):
        validated_arg_1 = request.parsed_params["validated_arg_1"]
        validated_arg_2 = request.parsed_params["validated_arg_2"]
        ...

Note that we're using our own view deriver (the ``schema`` argument to
``view_config``) to integrate our schemas and views, rather than using webargs's
``@use_args()`` / ``@use_kwargs()`` decorators. For the reasons for this see
commit message f61a5ff3cae6b983e24db809d8e4b4933aca1e92.

Validating requests-Library Responses
-------------------------------------

To validate a :mod:`requests`-library response you pass the response object to a
suitable validation schema's ``__init__()`` method and then call the schema's
``parse()`` method::

    import requests

    response = requests.get(...)

    try:
        parsed_params = BarSchema(response).parse()
    except lms.validation.ValidationError as err:
        ...
"""
from lms.validation._api import (
    APIReadResultSchema,
    APIRecordResultSchema,
    APIRecordSpeedgraderSchema,
)
from lms.validation._base import (
    PlainSchema,
    PyramidRequestSchema,
    RequestsResponseSchema,
)
from lms.validation._canvas import (
    CanvasListFilesResponseSchema,
    CanvasPublicURLResponseSchema,
)
from lms.validation._exceptions import LTIToolRedirect, ValidationError
from lms.validation._lti_launch_params import (
    LaunchParamsSchema,
    LaunchParamsURLConfiguredSchema,
)
from lms.validation._module_item_configuration import ConfigureModuleItemSchema

__all__ = (
    "APIRecordSpeedgraderSchema",
    "APIReadResultSchema",
    "APIRecordResultSchema",
    "PlainSchema",
    "PyramidRequestSchema",
    "RequestsResponseSchema",
    "ConfigureModuleItemSchema",
    "CanvasListFilesResponseSchema",
    "CanvasPublicURLResponseSchema",
    "LaunchParamsSchema",
    "LaunchParamsURLConfiguredSchema",
    "ValidationError",
    "LTIToolRedirect",
)


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
            request.parsed_params = info.options["schema"](request).parse()

            # Call the view normally.
            return view(context, request)

        return wrapper_view
    return view


def includeme(config):
    _validated_view.options = ["schema"]
    config.add_view_deriver(_validated_view)
