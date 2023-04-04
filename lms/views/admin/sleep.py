from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.tasks.email_digests import sleep


@view_defaults(route_name="admin.sleep", permission=Permissions.ADMIN)
class AdminSleepViews:
    def __init__(self, request):
        self.request = request

    @view_config(
        route_name="admin.sleep",
        request_method="GET",
        renderer="lms:templates/admin/sleep.html.jinja2",
    )
    def get(self):
        return {}

    @view_config(route_name="admin.sleep", request_method="POST")
    def post(self):
        seconds = int(self.request.POST["seconds"].strip())
        sleep.delay(seconds)
        return HTTPFound(location=self.request.route_url("admin.sleep"))
