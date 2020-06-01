"""Default traversal resources."""
from pyramid.security import Allow


class DefaultResource:
    """The application's default root resource."""

    __acl__ = [
        (Allow, "report_viewers", "view"),
        (Allow, "lti_user", "canvas_api"),
        (Allow, "lti_user", "lti_outcomes"),
        (Allow, "lti_user", "sync_api"),
    ]

    def __init__(self, request):
        """Return the default root resource object."""
        self._request = request
