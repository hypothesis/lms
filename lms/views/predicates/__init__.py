"""
Custom Pyramid view predicates.

See:

https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#view-and-route-predicates
"""
from lms.views.predicates._lti_launch import (
    AuthorizedToConfigureAssignments,
    BlackboardCopied,
    BrightspaceCopied,
    CanvasFile,
    Configured,
    DBConfigured,
    LegacySpeedGrader,
    URLConfigured,
    VitalSourceBook,
)


def includeme(config):
    for view_predicate_factory in (
        DBConfigured,
        BlackboardCopied,
        BrightspaceCopied,
        CanvasFile,
        URLConfigured,
        VitalSourceBook,
        Configured,
        AuthorizedToConfigureAssignments,
        LegacySpeedGrader,
    ):
        config.add_view_predicate(view_predicate_factory.name, view_predicate_factory)
