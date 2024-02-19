from pyramid.view import view_config

from lms.security import Permissions


class AdminEmailViews:
    def __init__(self, request):
        self.request = request

    @view_config(
        route_name="admin.analytics",
        permission=Permissions.STAFF,
        request_method="GET",
        renderer="lms:templates/admin/analytics.html.jinja2",
    )
    def get(self):
        return {}
