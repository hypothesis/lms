"""
Custom Pyramid view predicates.

See:

https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#view-and-route-predicates
"""
from lms.views.predicates._lti_launch import IsDBConfigured
from lms.views.predicates._lti_launch import IsCanvasFile
from lms.views.predicates._lti_launch import IsURLConfigured
from lms.views.predicates._lti_launch import IsConfigured
from lms.views.predicates._lti_launch import UserIsAuthorizedToConfigureAssignments


__all__ = [
    "IsDBConfigured",
    "IsCanvasFile",
    "IsURLConfigured",
    "IsConfigured",
    "UserIsAuthorizedToConfigureAssignments",
]


def includeme(config):
    for view_predicate_factory in (
        IsDBConfigured,
        IsCanvasFile,
        IsURLConfigured,
        IsConfigured,
        UserIsAuthorizedToConfigureAssignments,
    ):
        config.add_view_predicate(view_predicate_factory.name, view_predicate_factory)
