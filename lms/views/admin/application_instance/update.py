from marshmallow import fields, validate
from pyramid.settings import asbool
from pyramid.view import view_config

from lms.security import Permissions
from lms.services.aes import AESService
from lms.validation._base import PyramidRequestSchema
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


class UpdateApplicationInstanceView(BaseApplicationInstanceView):
    def __init__(self, request):
        super().__init__(request)

        self._aes_service = request.find_service(AESService)

    @view_config(
        route_name="admin.instance",
        request_method="POST",
        require_csrf=True,
        permission=Permissions.ADMIN,
    )
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
