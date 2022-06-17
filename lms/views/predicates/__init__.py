"""
Custom Pyramid view predicates.

See:

https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#view-and-route-predicates
"""

from dataclasses import dataclass
from functools import partial
from typing import Any

from lms.views.predicates import _predicates as predicates
from lms.views.predicates._predicates import ResourceLinkParam


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


PREDICATES = {
    "db_configured": predicates.is_db_configured,
    "blackboard_copied": predicates.is_blackboard_copied,
    "brightspace_copied": predicates.is_brightspace_copied,
    "url_configured_param": predicates.get_url_configured_param,
    "configured": predicates.is_configured,
    "authorized_to_configure_assignments": predicates.is_authorized_to_configure_assignments,
}


def includeme(config):
    for name, comparison in PREDICATES.items():
        config.add_view_predicate(
            name=name, factory=partial(Predicate, name=name, comparison=comparison)
        )
