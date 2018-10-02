from pyramid.security import Allow


class Root:
    """The default root factory for the application."""

    __acl__ = [(Allow, 'report_viewers', 'view')]

    def __init__(self, request):
        """Return the default root resource object."""
        self.request = request
