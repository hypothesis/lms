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
from lms.views.decorators.h_api import upsert_h_user
from lms.views.decorators.h_api import upsert_course_group
from lms.views.decorators.h_api import add_user_to_group
from lms.views.decorators.reports import report_lti_launch

__all__ = (
    "upsert_h_user",
    "upsert_course_group",
    "add_user_to_group",
    "report_lti_launch",
)
