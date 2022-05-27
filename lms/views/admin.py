from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import (
    forbidden_view_config,
    notfound_view_config,
    view_config,
    view_defaults,
)
from sqlalchemy.exc import IntegrityError

from lms.models import ApplicationInstance, LTIRegistration
from lms.security import Permissions
from lms.services import ApplicationInstanceNotFound, LTIRegistrationService


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
        self.application_instance_service = request.find_service(
            name="application_instance"
        )
        self.lti_registration_service: LTIRegistrationService = request.find_service(
            LTIRegistrationService
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
        route_name="admin.instance.new.registration",
        request_method="GET",
        renderer="lms:templates/admin/instance.new.registration.html.jinja2",
    )
    def instance_new_registration(self):  # pylint: disable=no-self-use
        return {}

    @view_config(
        route_name="admin.instance.new.registration",
        request_method="POST",
        renderer="lms:templates/admin/instance.new.html.jinja2",
    )
    def instance_new_registration_post(self):
        self._check_required_and_redirect(
            ["issuer", "client_id"],
            "admin.instance.new.registration",
        )

        lti_registration = self.lti_registration_service.get(
            self.request.params["issuer"], self.request.params["client_id"]
        )
        if not lti_registration:
            lti_registration = LTIRegistration(
                issuer=self.request.params["issuer"],
                client_id=self.request.params["client_id"],
            )
        return {
            "lti_registration": lti_registration,
        }

    @view_config(
        route_name="admin.instance.new",
        request_method="POST",
    )
    def instance_new(self):
        self._check_required_and_redirect(
            ["lms_url", "email", "deployment_id"],
            "admin.instance.new.registration",
        )

        lti_registration_id = self.request.params.get("lti_registration_id")
        if not lti_registration_id:
            self._check_required_and_redirect(
                ["auth_login_url", "key_set_url", "token_url"],
                "admin.instance.new.registration",
            )

            lti_registration_id = self.lti_registration_service.create(
                issuer=self.request.params["issuer"],
                client_id=self.request.params["client_id"],
                auth_login_url=self.request.params["auth_login_url"],
                key_set_url=self.request.params["key_set_url"],
                token_url=self.request.params["token_url"],
            ).id

        try:
            ai = self.application_instance_service.create(
                lms_url=self.request.params["lms_url"],
                email=self.request.params["email"],
                deployment_id=self.request.params["deployment_id"],
                developer_key=self.request.params.get("developer_key"),
                developer_secret=self.request.params.get("developer_secret"),
                lti_registration_id=lti_registration_id,
            )

        except IntegrityError:
            self.request.session.flash(
                f"Application instance with deployment_id: {self.request.params['deployment_id']} already exists",
                "errors",
            )
            return HTTPFound(
                location=self.request.route_url("admin.instance.new.registration")
            )

        return HTTPFound(
            location=self.request.route_url("admin.instance.id", id_=ai.id)
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

    def _check_required_and_redirect(self, fields, redirect_to):
        if not all((self.request.params.get(param) for param in fields)):
            self.request.session.flash(f"{fields} are required", "errors")
            raise HTTPFound(location=self.request.route_url(redirect_to))
