from marshmallow import validate
from pyramid.httpexceptions import HTTPClientError, HTTPFound, HTTPNotFound
from pyramid.view import view_config, view_defaults
from sqlalchemy.exc import IntegrityError
from webargs import fields

from lms.models import ApplicationInstance
from lms.models.public_id import InvalidPublicId
from lms.security import Permissions
from lms.services import ApplicationInstanceNotFound, LTIRegistrationService
from lms.services.aes import AESService
from lms.validation._base import PyramidRequestSchema, ValidationError
from lms.views.admin import flash_validation
from lms.views.admin._schemas import EmptyStringInt


class NewAppInstanceSchema(PyramidRequestSchema):
    """Schema for creating a new application instance."""

    location = "form"

    developer_key = fields.Str(required=False, allow_none=True)
    developer_secret = fields.Str(required=False, allow_none=True)

    name = fields.Str(required=True, validate=validate.Length(min=1))
    lms_url = fields.URL(required=True)
    email = fields.Email(required=True)
    organization_public_id = fields.Str(required=True, validate=validate.Length(min=1))


class NewAppInstanceSchemaV13(NewAppInstanceSchema):
    """Schema for creating a new LTI 1.3 application instance."""

    deployment_id = fields.Str(required=True, validate=validate.Length(min=1))
    lti_registration_id = fields.Str(required=True)


class UpdateApplicationInstanceSchema(PyramidRequestSchema):
    """Schema for updating an application instance."""

    location = "form"

    name = fields.Str(required=True, validate=validate.Length(min=1))
    lms_url = fields.URL(required=False)
    deployment_id = fields.Str(required=False)
    developer_key = fields.Str(required=False)
    developer_secret = fields.Str(required=False)


class UpgradeApplicationInstanceSchema(PyramidRequestSchema):
    location = "form"

    consumer_key = fields.Str(required=True, validate=validate.Length(min=1))
    deployment_id = fields.Str(required=True, validate=validate.Length(min=1))


class SearchApplicationInstanceSchema(PyramidRequestSchema):
    location = "form"

    # Max value for postgres `integer` type
    id = EmptyStringInt(required=False, validate=validate.Range(max=2147483647))
    name = fields.Str(required=False)
    consumer_key = fields.Str(required=False)
    issuer = fields.Str(required=False)
    client_id = fields.Str(required=False)
    deployment_id = fields.Str(required=False)
    tool_consumer_instance_guid = fields.Str(required=False)


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
        self._aes_service = request.find_service(AESService)

    @view_config(
        route_name="admin.instance.new",
        renderer="lms:templates/admin/instance.new.html.jinja2",
    )
    def new_instance_start(self):
        """Show the page to kick off creating a new application instance."""

        lti_registration = None
        if lti_registration_id := self.request.params.get("lti_registration_id"):
            lti_registration = self.lti_registration_service.get_by_id(
                lti_registration_id.strip()
            )

        return dict(self.request.params, lti_registration=lti_registration)

    @view_config(route_name="admin.instance.new", request_method="POST")
    def new_instance_callback(self):
        """Create an application instance (callback from the new AI page)."""

        lti_registration_id = self.request.params.get("lti_registration_id", "").strip()
        lti_registration_id = int(lti_registration_id) if lti_registration_id else None

        if flash_validation(
            self.request,
            NewAppInstanceSchemaV13 if lti_registration_id else NewAppInstanceSchema,
        ):
            # Looks like something went wrong!
            return self._redirect("admin.instance.new", _query=self.request.params)

        try:
            ai = self.application_instance_service.create_application_instance(
                name=self.request.params["name"].strip(),
                lms_url=self.request.params["lms_url"].strip(),
                email=self.request.params["email"].strip(),
                deployment_id=self.request.params.get("deployment_id", "").strip(),
                developer_key=self.request.params.get("developer_key", "").strip(),
                developer_secret=self.request.params.get(
                    "developer_secret", ""
                ).strip(),
                organization_public_id=self.request.params.get(
                    "organization_public_id", ""
                ).strip(),
                lti_registration_id=lti_registration_id,
            )
        except InvalidPublicId as err:
            self.request.session.flash(
                {"organization_public_id": [str(err)]}, "validation"
            )

            return self._redirect("admin.instance.new", _query=self.request.params)
        except IntegrityError:
            self.request.session.flash(
                f"Application instance with deployment_id: {self.request.params['deployment_id']} already exists",
                "errors",
            )

            return self._redirect("admin.instance.new", _query=self.request.params)

        return self._redirect("admin.instance", id_=ai.id)

    @view_config(
        route_name="admin.instance.upgrade",
        renderer="lms:templates/admin/instance.upgrade.html.jinja2",
    )
    def upgrade_instance_start(self):
        if lti_registration_id := self.request.params.get("lti_registration_id"):
            lti_registration = self.lti_registration_service.get_by_id(
                lti_registration_id.strip()
            )
        else:
            # This shouldn't really happen, but belt and braces
            raise HTTPClientError("`lti_registration_id` is required for an upgrade")

        return dict(self.request.params, lti_registration=lti_registration)

    @view_config(route_name="admin.instance.upgrade", request_method="POST")
    def upgrade_instance_callback(self):
        if flash_validation(self.request, UpgradeApplicationInstanceSchema):
            return self._redirect("admin.instance.upgrade", _query=self.request.params)

        consumer_key = self.request.params["consumer_key"].strip()
        deployment_id = self.request.params["deployment_id"].strip()

        # Find the Application instance we are upgrading
        try:
            application_instance = (
                self.application_instance_service.get_by_consumer_key(consumer_key)
            )
        except ApplicationInstanceNotFound:
            self.request.session.flash(
                f"Can't find application instance: '{consumer_key}' for upgrade.",
                "errors",
            )

            return self._redirect("admin.instance.upgrade", _query=self.request.params)

        # Don't allow to change instances that already on 1.3
        if application_instance.lti_version == "1.3.0":
            self.request.session.flash(
                f"Application instance: '{consumer_key}' is already on LTI 1.3.",
                "errors",
            )

            return self._redirect("admin.instance.upgrade", _query=self.request.params)
        # Set the LTI1.3 values
        application_instance.lti_registration = self.lti_registration_service.get_by_id(
            self.request.params.get("lti_registration_id", "").strip()
        )
        application_instance.deployment_id = deployment_id
        try:
            # Flush here to find if we are making a duplicate in the process of
            # upgrading
            self.request.db.flush()
        except IntegrityError:
            # Leave a clean transaction, otherwise  we get a:
            #   "PendingRollbackError: This Session's transaction has been
            #   rolled back due to a previous exception during flush."
            self.request.db.rollback()

            self.request.session.flash(
                f"Application instance with deployment_id: {self.request.params['deployment_id']} already exists",
                "errors",
            )

            return self._redirect("admin.instance.upgrade", _query=self.request.params)

        return self._redirect("admin.instance", id_=application_instance.id)

    @view_config(route_name="admin.instance.downgrade", request_method="POST")
    def downgrade_instance(self):
        ai = self._get_ai_or_404(self.request.matchdict["id_"])

        if ai.lti_version != "1.3.0":
            self.request.session.flash(
                f"Application instance: '{ai.id}' is not on LTI 1.3.", "errors"
            )
        elif not ai.consumer_key:
            self.request.session.flash(
                f"Application instance: '{ai.id}' doesn't have a consumer key to fallback to.",
                "errors",
            )
        else:
            ai.lti_registration_id = None
            ai.deployment_id = None

            self.request.session.flash("Downgraded LTI 1.1 successful", "messages")

        return self._redirect("admin.instance", id_=ai.id)

    @view_config(
        route_name="admin.instance.search",
        renderer="lms:templates/admin/instance.search.html.jinja2",
    )
    def search_start(self):
        return {}

    @view_config(
        route_name="admin.instance.search",
        request_method="POST",
        require_csrf=True,
        renderer="lms:templates/admin/instance.search.html.jinja2",
    )
    def search_callback(self):
        if flash_validation(self.request, SearchApplicationInstanceSchema):
            return {}

        instances = self.application_instance_service.search(
            id_=self.request.params.get("id"),
            name=self.request.params.get("name"),
            consumer_key=self.request.params.get("consumer_key"),
            issuer=self.request.params.get("issuer"),
            client_id=self.request.params.get("client_id"),
            deployment_id=self.request.params.get("deployment_id"),
            tool_consumer_instance_guid=self.request.params.get(
                "tool_consumer_instance_guid"
            ),
            email=self.request.params.get("email"),
        )

        return {"instances": instances}

    @view_config(
        route_name="admin.instance",
        renderer="lms:templates/admin/instance.html.jinja2",
    )
    def show_instance(self):
        ai = self._get_ai_or_404(self.request.matchdict["id_"])
        return {"instance": ai}

    @view_config(
        route_name="admin.instance.move_org",
        request_method="POST",
        require_csrf=True,
    )
    def move_application_instance_org(self):
        ai = self._get_ai_or_404(self.request.matchdict["id_"])

        try:
            self.application_instance_service.update_application_instance(
                ai,
                organization_public_id=self.request.params.get(
                    "org_public_id", ""
                ).strip(),
            )
            self.request.session.flash(
                f"Updated application instance {ai.id}", "messages"
            )
        except ValidationError as err:
            self.request.session.flash(err.messages, "validation")

        return self._redirect("admin.instance", id_=ai.id)

    @view_config(route_name="admin.instance", request_method="POST", require_csrf=True)
    def update_instance(self):
        ai = self._get_ai_or_404(self.request.matchdict["id_"])

        if flash_validation(self.request, UpdateApplicationInstanceSchema):
            # Looks like something went wrong!
            return self._redirect("admin.instance", id_=ai.id)

        self.application_instance_service.update_application_instance(
            ai,
            name=self.request.params.get("name", "").strip(),
            lms_url=self.request.params.get("lms_url", "").strip(),
            deployment_id=self.request.params.get("deployment_id", "").strip(),
            developer_key=self.request.params.get("developer_key", "").strip(),
            developer_secret=self.request.params.get("developer_secret", "").strip(),
        )

        # Helper to declare settings as secret
        aes_secret = object()

        for setting, sub_setting, setting_type in (
            ("blackboard", "files_enabled", bool),
            ("blackboard", "groups_enabled", bool),
            ("canvas", "sections_enabled", bool),
            ("canvas", "groups_enabled", bool),
            ("desire2learn", "client_id", str),
            ("desire2learn", "client_secret", aes_secret),
            ("desire2learn", "groups_enabled", bool),
            ("desire2learn", "files_enabled", bool),
            ("desire2learn", "create_line_item", bool),
            ("microsoft_onedrive", "files_enabled", bool),
            ("vitalsource", "enabled", bool),
            ("vitalsource", "user_lti_param", str),
            ("vitalsource", "user_lti_pattern", str),
            ("vitalsource", "api_key", str),
            ("vitalsource", "disable_licence_check", bool),
            ("jstor", "enabled", bool),
            ("jstor", "site_code", str),
            ("hypothesis", "notes", str),
        ):
            value = self.request.params.get(f"{setting}.{sub_setting}")
            if setting_type == bool:
                value = value == "on"
                ai.settings.set(setting, sub_setting, value)
            elif setting_type == aes_secret:
                value = value.strip() if value else None
                if not value:
                    continue

                ai.settings.set_secret(self._aes_service, setting, sub_setting, value)

            else:
                assert setting_type == str
                value = value.strip() if value else None
                ai.settings.set(setting, sub_setting, value)

        self.request.session.flash(f"Updated application instance {ai.id}", "messages")

        return self._redirect("admin.instance", id_=ai.id)

    def _redirect(self, route_name, **kwargs):
        return HTTPFound(location=self.request.route_url(route_name, **kwargs))

    def _get_ai_or_404(self, id_) -> ApplicationInstance:
        try:
            return self.application_instance_service.get_by_id(id_=id_)

        except ApplicationInstanceNotFound as err:
            raise HTTPNotFound() from err
