from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.renderers import render_to_response
from pyramid.view import view_config, view_defaults
from sqlalchemy.exc import IntegrityError

from lms.models import ApplicationInstance
from lms.security import Permissions
from lms.services import ApplicationInstanceNotFound, LTIRegistrationService
from lms.views.admin import flash_missing_fields


@view_defaults(request_method="GET", permission=Permissions.ADMIN)
class AdminApplicationInstanceViews:
    def __init__(self, request):
        self.request = request
        self.application_instance_service = request.find_service(
            name="application_instance"
        )
        self.lti_registration_service: LTIRegistrationService = request.find_service(
            LTIRegistrationService
        )

    @view_config(
        route_name="admin.instances",
        request_method="GET",
        renderer="lms:templates/admin/instances.html.jinja2",
    )
    def instances(self):
        return {}

    @view_config(
        route_name="admin.registration.new.instance",
        request_method="POST",
        renderer="lms:templates/admin/instance.new.html.jinja2",
    )
    def new_instance(self):
        lti_registration = self.lti_registration_service.get_by_id(
            self.request.matchdict["id_"]
        )

        if flash_missing_fields(self.request, ["deployment_id", "lms_url", "email"]):
            response = render_to_response(
                "lms:templates/admin/instance.new.html.jinja2",
                {"lti_registration": lti_registration.id},
                request=self.request,
            )
            response.status = 400
            return response

        try:
            ai = self.application_instance_service.create_application_instance(
                lms_url=self.request.params["lms_url"].strip(),
                email=self.request.params["email"].strip(),
                deployment_id=self.request.params["deployment_id"].strip(),
                developer_key=self.request.params.get("developer_key", "").strip(),
                developer_secret=self.request.params.get(
                    "developer_secret", ""
                ).strip(),
                lti_registration_id=self.request.matchdict["id_"],
            )

        except IntegrityError:
            self.request.session.flash(
                f"Application instance with deployment_id: {self.request.params['deployment_id']} already exists",
                "errors",
            )
            response = render_to_response(
                "lms:templates/admin/instance.new.html.jinja2",
                {"lti_registration": lti_registration.id},
                request=self.request,
            )
            response.status = 400
            return response

        return HTTPFound(
            location=self.request.route_url("admin.instance.id", id_=ai.id)
        )

    @view_config(
        route_name="admin.instances.search",
        request_method="POST",
        require_csrf=True,
        renderer="lms:templates/admin/instances.html.jinja2",
    )
    def search(self):
        if not any(
            (
                self.request.params.get(param)
                for param in [
                    "consumer_key",
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
            consumer_key=self.request.params.get("consumer_key"),
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
            ("vitalsource", "lti_user_field", str),
            ("vitalsource", "api_key", str),
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
