from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound
from pyramid.view import (
    forbidden_view_config,
    notfound_view_config,
    view_config,
    view_defaults,
)

from lms.models import ApplicationInstance
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
        request_method="GET",
        renderer="lms:templates/admin/instances.html.jinja2",
    )
    def instances(self):  # pylint: disable=no-self-use
        return {}

    @view_config(
        route_name="admin.instances.consumer_key",
        request_method="POST",
        require_csrf=True,
    )
    def find_by_consumer_key(self):
        try:
            consumer_key = self.request.params["consumer_key"]
        except KeyError as err:
            raise HTTPBadRequest() from err

        try:
            ai = self.application_instance_service.get_by_consumer_key(consumer_key)
        except ApplicationInstanceNotFound:
            self.request.session.flash(
                f'No application instance found for {self.request.params["consumer_key"]}',
                "errors",
            )
            return HTTPFound(location=self.request.route_url("admin.instances"))

        return HTTPFound(
            location=self.request.route_url(
                "admin.instance.consumer_key", consumer_key=ai.consumer_key
            ),
        )

    @view_config(
        route_name="admin.instances.search",
        request_method="POST",
        require_csrf=True,
        renderer="lms:templates/admin/instances.results.html.jinja2",
    )
    def search(self):
        if not any(
            (
                self.request.params.get(param)
                for param in [
                    "issuer",
                    "client_id",
                    "deployment_id",
                    "tool_consumer_instance_guid",
                ]
            )
        ):
            self.request.session.flash(
                "Need to pass at least one search criteria", "errors"
            )
            return HTTPFound(location=self.request.route_url("admin.instances"))

        instances = self.application_instance_service.search(
            issuer=self.request.params.get("issuer"),
            client_id=self.request.params.get("client_id"),
            deployment_id=self.request.params.get("deployment_id"),
            tool_consumer_instance_guid=self.request.params.get(
                "tool_consumer_instance_guid"
            ),
        )

        if not instances:
            self.request.session.flash("No instances found", "errors")
            return HTTPFound(location=self.request.route_url("admin.instances"))

        if len(instances) == 1:
            return HTTPFound(
                location=self.request.route_url(
                    "admin.instance.id", id_=instances[0].id
                )
            )

        return {"instances": instances}

    @view_config(
        route_name="admin.instance.id",
        renderer="lms:templates/admin/instance.html.jinja2",
    )
    @view_config(
        route_name="admin.instance.consumer_key",
        renderer="lms:templates/admin/instance.html.jinja2",
    )
    def show_instance(self):
        ai = self._get_ai_or_404(**self.request.matchdict)
        return {"instance": ai}

    @view_config(
        route_name="admin.instance.id",
        request_method="POST",
        require_csrf=True,
    )
    @view_config(
        route_name="admin.instance.consumer_key",
        request_method="POST",
        require_csrf=True,
    )
    def update_instance(self):
        ai = self._get_ai_or_404(**self.request.matchdict)

        for setting, sub_setting, setting_type in (
            ("canvas", "sections_enabled", bool),
            ("canvas", "groups_enabled", bool),
            ("blackboard", "files_enabled", bool),
            ("blackboard", "groups_enabled", bool),
            ("microsoft_onedrive", "files_enabled", bool),
            ("vitalsource", "enabled", bool),
            ("jstor", "enabled", bool),
            ("jstor", "site_code", str),
        ):
            value = self.request.params.get(f"{setting}.{sub_setting}")
            if setting_type == bool:
                value = value == "on"
            else:
                assert setting_type == str
                value = value.strip() if value else None

            ai.settings.set(setting, sub_setting, value)

        self.request.session.flash(f"Updated application instance {ai.id}", "messages")

        return HTTPFound(
            location=self.request.route_url("admin.instance.id", id_=ai.id)
        )

    def _get_ai_or_404(self, consumer_key=None, id_=None) -> ApplicationInstance:
        try:
            if consumer_key:
                return self.application_instance_service.get_by_consumer_key(
                    consumer_key
                )

            return self.application_instance_service.get_by_id(id_=id_)

        except ApplicationInstanceNotFound as err:
            raise HTTPNotFound() from err
