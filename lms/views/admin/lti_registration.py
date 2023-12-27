from urllib.parse import urlparse

from marshmallow import ValidationError, validate, validates
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.renderers import render_to_response
from pyramid.view import view_config, view_defaults
from sqlalchemy.exc import IntegrityError
from webargs import fields

from lms.models import LTIRegistration
from lms.security import Permissions
from lms.services import LTIRegistrationService
from lms.validation._base import PyramidRequestSchema
from lms.views.admin import flash_validation
from lms.views.admin._schemas import EmptyStringInt


class LTIRegistrationBaseSchema(PyramidRequestSchema):
    location = "form"

    issuer = fields.URL(required=True)
    client_id = fields.Str(required=True, validate=validate.Length(min=1))

    @validates("issuer")
    def validate_issuer(self, value):
        if value.endswith("/"):
            # Prevent confusion with application instance LMS URL.
            raise ValidationError("Issuer can't end with '/'")


class SearchLTIRegistrationSchema(PyramidRequestSchema):
    location = "form"

    # Max value for postgres `integer` type
    id = EmptyStringInt(required=False, validate=validate.Range(max=2147483647))
    issuer = fields.Str(required=False)
    client_id = fields.Str(required=False)


class UpdateLTIRegistrationSchema(PyramidRequestSchema):
    location = "form"

    auth_login_url = fields.URL(required=True)
    key_set_url = fields.URL(required=True)
    token_url = fields.URL(required=True)


class LTIRegistrationSchema(LTIRegistrationBaseSchema):
    location = "form"

    auth_login_url = fields.URL(required=True)
    key_set_url = fields.URL(required=True)
    token_url = fields.URL(required=True)


URL_SUGGESTIONS = {
    "https://blackboard.com": {
        "auth_login_url": "https://developer.blackboard.com/api/v1/gateway/oidcauth",
        "key_set_url": "https://developer.blackboard.com/api/v1/management/applications/{client_id}/jwks.json",
        "token_url": "https://developer.blackboard.com/api/v1/gateway/oauth2/jwttoken",
    },
    ".instructure.com": {
        "auth_login_url": "https://sso.canvaslms.com/api/lti/authorize_redirect",
        "key_set_url": "https://sso.canvaslms.com/api/lti/security/jwks",
        "token_url": "https://sso.canvaslms.com/login/oauth2/token",
    },
    ".brightspace.com": {
        "auth_login_url": "https://{issuer_host}/d2l/lti/authenticate",
        "key_set_url": "https://{issuer_host}/d2l/.well-known/jwks",
        "token_url": "https://{issuer_host}/core/connect/token",
    },
    ".moodlecloud.com": {
        "auth_login_url": "https://{issuer_host}/mod/lti/auth.php",
        "key_set_url": "https://{issuer_host}/mod/lti/certs.php",
        "token_url": "https://{issuer_host}/mod/lti/token.php",
    },
}


@view_defaults(request_method="GET", permission=Permissions.ADMIN)
class AdminLTIRegistrationViews:
    def __init__(self, request) -> None:
        self.request = request
        self.lti_registration_service: LTIRegistrationService = request.find_service(
            LTIRegistrationService
        )

    @view_config(
        route_name="admin.registrations",
        request_method="GET",
        renderer="lms:templates/admin/registrations.html.jinja2",
    )
    def registrations(self):
        return {}

    @view_config(
        route_name="admin.registration.new",
        request_method="GET",
        renderer="lms:templates/admin/registration.new.html.jinja2",
    )
    def new_registration(self):
        return {}

    @view_config(
        route_name="admin.registration.suggest_urls",
        request_method="POST",
        renderer="lms:templates/admin/registration.new.html.jinja2",
    )
    def suggest_lms_urls(self):
        if flash_validation(self.request, LTIRegistrationBaseSchema):
            self.request.response.status_code = 400
            return {}

        return self._get_url_suggestions(
            self.request.params["issuer"], self.request.params["client_id"]
        )

    @view_config(
        route_name="admin.registration.new",
        request_method="POST",
    )
    def new_registration_callback(self):
        params = self.request.params
        if flash_validation(self.request, LTIRegistrationSchema):
            response = render_to_response(
                "lms:templates/admin/registration.new.html.jinja2",
                {},
                request=self.request,
            )
            response.status_code = 400
            return response

        try:
            lti_registration = self.lti_registration_service.create_registration(
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
            response = render_to_response(
                "lms:templates/admin/registration.new.html.jinja2",
                {},
                request=self.request,
            )
            response.status_code = 400
            return response

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
        if flash_validation(self.request, SearchLTIRegistrationSchema):
            return {}

        registrations = self.lti_registration_service.search_registrations(
            id_=self.request.params.get("id"),
            issuer=self.request.params.get("issuer", "").strip(),
            client_id=self.request.params.get("client_id", "").strip(),
        )

        return {"registrations": registrations}

    @view_config(
        route_name="admin.registration.id",
        renderer="lms:templates/admin/registration.html.jinja2",
    )
    def show_registration(self):
        return {
            "registration": self._get_registration_or_404(self.request.matchdict["id_"])
        }

    @view_config(
        route_name="admin.registration.id",
        renderer="lms:templates/admin/registration.html.jinja2",
        request_method="POST",
        require_csrf=True,
    )
    def update_registration(self):
        lti_registration = self._get_registration_or_404(self.request.matchdict["id_"])
        if flash_validation(self.request, UpdateLTIRegistrationSchema):
            self.request.response.status_code = 400
            return {"registration": lti_registration}

        params = self.request.params
        lti_registration.auth_login_url = params["auth_login_url"].strip()
        lti_registration.key_set_url = params["key_set_url"].strip()
        lti_registration.token_url = params["token_url"].strip()

        self.request.session.flash("Updated registration", "messages")
        return {"registration": lti_registration}

    @staticmethod
    def _get_url_suggestions(issuer, client_id):
        """
        Get suggestion for the registration endpoints.

        Registration endpoints tend to be the same across the same LMS or at
        least be based on the issuer and client_id.
        """
        for suffix, url_templates in URL_SUGGESTIONS.items():
            if issuer.endswith(suffix):
                # For some LMS the path part of the URL is the same but
                # anchored in the same host as `issuer`
                issuer_host = urlparse(issuer).netloc

                return {
                    key: template.format(issuer_host=issuer_host, client_id=client_id)
                    for key, template in url_templates.items()
                }

        return {"auth_login_url": None, "key_set_url": None, "token_url": None}

    def _get_registration_or_404(self, id_) -> LTIRegistration:
        if org := self.lti_registration_service.get_by_id(id_):
            return org

        raise HTTPNotFound()
