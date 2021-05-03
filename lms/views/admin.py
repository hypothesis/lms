from pyramid.httpexceptions import HTTPFound
from pyramid.view import forbidden_view_config, view_config, view_defaults

from lms.security import Permissions


@forbidden_view_config(path_info="/admin/*")
def logged_out(request):
    return HTTPFound(location=request.route_url("pyramid_googleauth.login"))


@view_defaults(request_method="GET", permission=Permissions.ADMIN)
class AdminViews:
    def __init__(self, request):
        self.request = request
        self.application_instance_service = request.find_service(
            name="application_instance"
        )

    @view_config(
        route_name="admin.index",
    )  # pylint: disable=no-self-use
    def index(self):
        return HTTPFound(location=self.request.route_url("admin.installations"))

    @view_config(
        route_name="admin.installations",
        renderer="lms:templates/admin/installations.html.jinja2",
    )  # pylint: disable=no-self-use
    def installations(self):
        return {}

    @view_config(
        route_name="admin.installations",
        request_method="POST",
    )
    def find_installation(self):
        if "query" not in self.request.params:
            self.request.session.flash("Missing mandatory 'query'", "errors")
            return HTTPFound(location=self.request.route_url("admin.installations"))

        installation = self.application_instance_service.find(
            self.request.params["query"]
        )
        if installation:
            return HTTPFound(
                location=self.request.route_url(
                    "admin.installation", id=installation.id
                ),
            )
        self.request.session.flash(
            f'No installation found for {self.request.params["query"]}', "errors"
        )
        return HTTPFound(location=self.request.route_url("admin.installations"))

    @view_config(
        route_name="admin.installation",
        renderer="lms:templates/admin/installation.html.jinja2",
    )
    def show_installation(self):

        installation = self.application_instance_service.get(
            self.request.matchdict["id"]
        )
        return {"installation": installation}

    @view_config(
        route_name="admin.installation",
        request_method="POST",
    )
    def update_installation(self):
        installation = self.application_instance_service.get(
            self.request.matchdict["id"]
        )

        sections_enabled = (
            "sections_enabled" in self.request.params
            and self.request.params["sections_enabled"] == "on"
        )
        groups_enabled = (
            "groups_enabled" in self.request.params
            and self.request.params["groups_enabled"] == "on"
        )

        self.application_instance_service.update_settings(
            installation,
            canvas_sections_enabled=sections_enabled,
            canvas_groups_enabled=groups_enabled,
        )
        self.request.session.flash(
            f"Updated installation {installation.id}", "messages"
        )

        return HTTPFound(
            location=self.request.route_url("admin.installation", id=installation.id)
        )
