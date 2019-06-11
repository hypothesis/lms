"""Default traversal resources."""
from pyramid.security import Allow


__all__ = ["DefaultResource"]


class DefaultResource:
    """The application'a default root resource."""

    __acl__ = [(Allow, "report_viewers", "view"), (Allow, "lti_user", "canvas_api")]

    def __init__(self, request):
        """Return the default root resource object."""
        self._request = request
