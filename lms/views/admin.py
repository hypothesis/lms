from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound
from pyramid.view import (
    forbidden_view_config,
    notfound_view_config,
    view_config,
    view_defaults,
)

from lms.security import Permissions
from lms.services import ApplicationInstanceNotFound


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

    @view_config(route_name="admin.index")
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
        try:
            consumer_key = self.request.params["query"]
        except KeyError as err:
            raise HTTPBadRequest() from err

        try:
            ai = self.application_instance_service.get_by_consumer_key(consumer_key)
        except ApplicationInstanceNotFound:
            self.request.session.flash(
                f'No application instance found for {self.request.params["query"]}',
                "errors",
            )
            return HTTPFound(location=self.request.route_url("admin.instances"))

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

        for setting, sub_setting in (
            ("canvas", "sections_enabled"),
            ("canvas", "groups_enabled"),
            ("blackboard", "files_enabled"),
            ("microsoft_onedrive", "files_enabled"),
        ):
            enabled = self.request.params.get(f"{setting}.{sub_setting}") == "on"
            ai.settings.set(setting, sub_setting, enabled)

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
            return self.application_instance_service.get_by_consumer_key(consumer_key)
        except ApplicationInstanceNotFound as err:
            raise HTTPNotFound() from err
