"""Default traversal resources."""
from pyramid.security import Allow


class DefaultResource:  # pylint:disable=too-few-public-methods
    """The application's default root resource."""

    __acl__ = [
        (Allow, "report_viewers", "view"),
        (Allow, "lti_user", "canvas_api"),
        (Allow, "lti_user", "lti_outcomes"),
    ]

    def __init__(self, request):
        """Return the default root resource object."""
        self._request = request
