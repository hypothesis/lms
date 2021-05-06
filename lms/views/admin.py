from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound
from pyramid.view import (
    forbidden_view_config,
    notfound_view_config,
    view_config,
    view_defaults,
)

from lms.security import Permissions
from lms.services import ConsumerKeyError


@forbidden_view_config(path_info="/admin/*")
def logged_out(request):
    return HTTPFound(location=request.route_url("pyramid_googleauth.login"))


@notfound_view_config(path_info="/admin/*", append_slash=True)
def notfound(_request):
    return HTTPNotFound()


@view_defaults(request_method="GET", permission=Permissions.ADMIN)
class AdminViews:
    def __init__(self, request):
        self.request = request
        self.application_instance_service = request.find_service(
            name="application_instance"
        )

    @view_config(route_name="admin.index")  # pylint: disable=no-self-use
    def index(self):
        return HTTPFound(location=self.request.route_url("admin.instances"))

    @view_config(
        route_name="admin.instances",
        renderer="lms:templates/admin/instances.html.jinja2",
    )  # pylint: disable=no-self-use
    def instances(self):
        return {}

    @view_config(
        route_name="admin.instances",
        request_method="POST",
        require_csrf=True,
    )
    def find_instance(self):
        if "query" not in self.request.params:
            raise HTTPBadRequest()

        try:
            ai = self.application_instance_service.get(self.request.params["query"])
        except ConsumerKeyError:
            self.request.session.flash(
                f'No application instance found for {self.request.params["query"]}',
                "errors",
            )
            return HTTPFound(location=self.request.route_url("admin.instances"))
        else:
            return HTTPFound(
                location=self.request.route_url(
                    "admin.instance", consumer_key=ai.consumer_key
                ),
            )

    @view_config(
        route_name="admin.instance",
        renderer="lms:templates/admin/instance.html.jinja2",
    )
    def show_instance(self):
        ai = self._get_ai_or_404(self.request.matchdict["consumer_key"])
        return {"instance": ai}

    @view_config(
        route_name="admin.instance",
        request_method="POST",
        require_csrf=True,
    )
    def update_instance(self):
        ai = self._get_ai_or_404(self.request.matchdict["consumer_key"])

        sections_enabled = (
            "sections_enabled" in self.request.params
            and self.request.params["sections_enabled"] == "on"
        )
        groups_enabled = (
            "groups_enabled" in self.request.params
            and self.request.params["groups_enabled"] == "on"
        )

        self.application_instance_service.update_settings(
            ai,
            canvas_sections_enabled=sections_enabled,
            canvas_groups_enabled=groups_enabled,
        )
        self.request.session.flash(
            f"Updated application instance {ai.consumer_key}", "messages"
        )

        return HTTPFound(
            location=self.request.route_url(
                "admin.instance", consumer_key=ai.consumer_key
            )
        )

    def _get_ai_or_404(self, consumer_key):
        try:
            return self.application_instance_service.get(consumer_key)
        except ConsumerKeyError as err:
            raise HTTPNotFound() from err
