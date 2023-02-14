from marshmallow import fields, validate
from pyramid.settings import asbool
from pyramid.view import view_config

from lms.services.aes import AESService
from lms.validation._base import PyramidRequestSchema, ValidationError
from lms.views.admin import flash_validation
from lms.views.admin.application_instance._core import (
    AES_SECRET,
    APPLICATION_INSTANCE_SETTINGS,
    BaseApplicationInstanceView,
)


class UpdateApplicationInstanceSchema(PyramidRequestSchema):
    """Schema for updating an application instance."""

    location = "form"

    name = fields.Str(required=True, validate=validate.Length(min=1))
    lms_url = fields.URL(required=False)
    deployment_id = fields.Str(required=False)
    developer_key = fields.Str(required=False)
    developer_secret = fields.Str(required=False)


class AdminApplicationInstanceViews(BaseApplicationInstanceView):
    def __init__(self, request):
        super().__init__(request)

        self._aes_service = request.find_service(AESService)

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
        route_name="admin.instance",
        renderer="lms:templates/admin/application_instance/show.html.jinja2",
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

        for (
            setting,
            sub_setting,
        ), setting_type in APPLICATION_INSTANCE_SETTINGS.items():
            value = self.request.params.get(f"{setting}.{sub_setting}")
            value = value.strip() if value else None

            if setting_type is asbool:
                value = value == "on"
                ai.settings.set(setting, sub_setting, value)

            elif setting_type == AES_SECRET:
                if not value:
                    continue

                ai.settings.set_secret(self._aes_service, setting, sub_setting, value)

            else:
                assert setting_type == str
                ai.settings.set(setting, sub_setting, value)

        self.request.session.flash(f"Updated application instance {ai.id}", "messages")

        return self._redirect("admin.instance", id_=ai.id)
