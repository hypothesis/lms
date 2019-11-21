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
from lms.views.decorators.lis_result_sourcedid import upsert_lis_result_sourcedid

__all__ = ("upsert_lis_result_sourcedid",)
