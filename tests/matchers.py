"""Objects that compare equal to other objects for testing."""

from h_matchers import Any
from pyramid.response import Response


def temporary_redirect_to(location):
    """Return a matcher for any `HTTP 302 Found` redirect to the given URL."""
    return Any.instance_of(Response).with_attrs(
        {"status_code": 302, "location": location}
    )
