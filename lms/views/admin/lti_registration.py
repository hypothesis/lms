from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import render_to_response
from pyramid.view import view_config, view_defaults
from sqlalchemy.exc import IntegrityError

from lms.security import Permissions
from lms.services import LTIRegistrationService
from lms.views.admin import flash_missing_fields


@view_defaults(request_method="GET", permission=Permissions.ADMIN)
class AdminLTIRegistrationViews:
    def __init__(self, request):
        self.request = request
        self.lti_registration_service: LTIRegistrationService = request.find_service(
            LTIRegistrationService
        )

    @view_config(
        route_name="admin.registrations",
        request_method="GET",
        renderer="lms:templates/admin/registrations.html.jinja2",
    )
    def registrations(self):  # pylint: disable=no-self-use
        return {}

    @view_config(
        route_name="admin.registration.new",
        request_method="GET",
        renderer="lms:templates/admin/registration.new.html.jinja2",
    )
    def registration_new(self):  # pylint: disable=no-self-use
        return {}

    @view_config(
        route_name="admin.registration.new",
        request_method="POST",
    )
    def registration_new_post(self):
        params = self.request.params

        if flash_missing_fields(
            self.request,
            ["issuer", "client_id", "auth_login_url", "key_set_url", "token_url"],
        ):
            response = render_to_response(
                "lms:templates/admin/registration.new.html.jinja2",
                {},
                request=self.request,
            )
            response.status_code = 400
            return response

        try:
            lti_registration = self.lti_registration_service.create(
                issuer=params["issuer"].strip(),
                client_id=params["client_id"].strip(),
                auth_login_url=params["auth_login_url"].strip(),
                key_set_url=params["key_set_url"].strip(),
                token_url=params["token_url"].strip(),
            )
        except IntegrityError:
            self.request.session.flash(
                f"Registration {params['issuer']} / {params['client_id']} already exists",
                "errors",
            )
            return HTTPFound(location=self.request.route_url("admin.registration.new"))

        return HTTPFound(
            location=self.request.route_url(
                "admin.registration.id", id_=lti_registration.id
            )
        )

    @view_config(
        route_name="admin.registrations.search",
        request_method="POST",
        require_csrf=True,
        renderer="lms:templates/admin/registrations.html.jinja2",
    )
    def search(self):
        if not any(
            (self.request.params.get(param) for param in ["issuer", "client_id"])
        ):
            self.request.session.flash(
                "Need to pass at least one search criteria", "errors"
            )
            return HTTPFound(location=self.request.route_url("admin.registrations"))

        registrations = self.lti_registration_service.search(
            issuer=self.request.params.get("issuer"),
            client_id=self.request.params.get("client_id"),
        )

        if registrations and len(registrations) == 1:
            return HTTPFound(
                location=self.request.route_url(
                    "admin.registration.id", id_=registrations[0].id
                )
            )

        return {"registrations": registrations}

    @view_config(
        route_name="admin.registration.id",
        renderer="lms:templates/admin/registration.html.jinja2",
    )
    def show_registration(self):
        return {
            "registration": self.lti_registration_service.get_by_id(
                self.request.matchdict["id_"]
            )
        }

    @view_config(
        route_name="admin.registration.new.instance",
        request_method="GET",
        renderer="lms:templates/admin/instance.new.html.jinja2",
    )
    def registration_new_instance(self):
        return {
            "lti_registration": self.lti_registration_service.get_by_id(
                self.request.matchdict["id_"]
            )
        }
