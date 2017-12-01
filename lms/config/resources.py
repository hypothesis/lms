from pyramid.security import Allow


class Root(object):
    """Create list of users and what they are allowed to access."""

    __acl__ = [(Allow, 'report_viewer', 'view')]

    def __init__(self, request):
        """Pass."""
        pass
