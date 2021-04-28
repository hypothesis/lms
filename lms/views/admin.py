from http.cookies import SimpleCookie

from pyramid.httpexceptions import HTTPFound
from pyramid.view import forbidden_view_config, view_config, view_defaults

from lms.security import Permissions


@view_defaults(request_method="GET")
class AdminViews:
    def __init__(self, request):
        self.request = request

    @view_config(
        route_name="admin.index",
        renderer="lms:templates/admin/index.html.jinja2",
        permission=Permissions.ADMIN,
    )
    def index(self):
        cookie = SimpleCookie()
        cookie.load(self.request.headers["Cookie"])
        return {"session": cookie["session"].value}

    @forbidden_view_config()
    def logged_out(self):
        return HTTPFound(location=self.request.route_url("pyramid_googleauth.login"))
