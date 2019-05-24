"""
Custom view decorators.

These are Pyramid view decorators, to be used with the ``decorators`` view
config parameter. For example:

    @view_config(
        ...,
        decorator=[
            "lms.views.decorators.decorator_2",
            "lms.views.decorators.decorator_1",
        ]
    )
    def my_view(context, request):
        ...

For documentation see:

https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/viewconfig.html#non-predicate-arguments
"""
from lms.views.decorators.reports import report_lti_launch

from lms.views.decorators.legacy_h_api import legacy_upsert_h_user
from lms.views.decorators.legacy_h_api import legacy_create_course_group
from lms.views.decorators.legacy_h_api import legacy_add_user_to_group

__all__ = (
    "report_lti_launch",
    # Legacy view decorators. These are used as normal Python @decorators
    # applied directly to the view function, rather than with Pyramid's
    # decorators= view config parameter. See the docstring in
    # lms/views/decorators/legacy_h_api.py for details.
    "legacy_upsert_h_user",
    "legacy_create_course_group",
    "legacy_add_user_to_group",
)
