"""
Custom Pyramid view predicates for the Basic LTI Launch view.

See:
https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#view-and-route-predicates
"""

from dataclasses import dataclass
from functools import partial
from typing import Any

from lms.services.document_url import DocumentURLService


@dataclass
class Predicate:
    """A predicate which wraps a simple function and compares it to a value."""

    value: Any
    info: Any
    name: str
    comparison: callable

    def text(self):
        """Get a string describing the behavior of this predicate."""

        # Used by Pyramid in error messages.
        return f"{self.name} = {self.value}"

    def phash(self):
        """Get a string uniquely identifying the name and value."""

        # Used by Pyramid for view configuration constraints handling.
        return self.text()

    def __call__(self, context, request):
        """Get whether our comparison matches our configuration."""

        value = self.comparison(context, request)

        # If you set a predicate to None, Pyramid disables it, so to match this
        # we will accept matches on anything falsy as well as matching values.
        return (value == self.value) or (not value and not self.value)


def has_document_url(context, request):
    return bool(
        request.find_service(DocumentURLService).get_document_url(context, request)
    )


def is_authorized_to_configure_assignments(_context, request):
    """Get if the current user allowed to configured assignments."""

    if not request.lti_user:
        return False

    roles = request.lti_user.roles.lower()

    return any(
        role in roles for role in ["administrator", "instructor", "teachingassistant"]
    )


PREDICATES = {
    "has_document_url": has_document_url,
    "authorized_to_configure_assignments": is_authorized_to_configure_assignments,
}


def includeme(config):
    for name, comparison in PREDICATES.items():
        config.add_view_predicate(
            name=name, factory=partial(Predicate, name=name, comparison=comparison)
        )
