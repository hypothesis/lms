"""
Custom Pyramid view predicates.

See:

https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#view-and-route-predicates
"""
from lms.views.predicates._lti_launch import (
    AuthorizedToConfigureAssignments,
    BlackboardCopied,
    CanvasFile,
    Configured,
    DBConfigured,
    URLConfigured,
)


def includeme(config):
    for view_predicate_factory in (
        DBConfigured,
        BlackboardCopied,
        CanvasFile,
        URLConfigured,
        Configured,
        AuthorizedToConfigureAssignments,
    ):
        config.add_view_predicate(view_predicate_factory.name, view_predicate_factory)
