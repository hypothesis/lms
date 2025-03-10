from marshmallow import fields, validate
from pyramid.settings import asbool
from pyramid.view import view_config

from lms.models import ApplicationSettings
from lms.models.json_settings import JSONSetting
from lms.security import Permissions
from lms.services.aes import AESService
from lms.validation._base import PyramidRequestSchema
from lms.views.admin import flash_validation
from lms.views.admin.application_instance._core import BaseApplicationInstanceView


class UpdateApplicationInstanceSchema(PyramidRequestSchema):
    """Schema for updating an application instance."""

    location = "form"

    name = fields.Str(required=True, validate=validate.Length(min=1))
    lms_url = fields.URL(required=False)
    deployment_id = fields.Str(required=False)


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
        ai = self.application_instance

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

        # Notes are displayed in the main info tab but are stored alongside notes
        notes = self.request.params.get("hypothesis.notes")
        notes = notes.strip() if notes else None
        ai.settings.set("hypothesis", "notes", notes)

        self.request.session.flash(f"Updated application instance {ai.id}", "messages")
        return self._redirect("admin.instance", id_=ai.id)

    @view_config(
        route_name="admin.instance.section",
        match_param="section=settings",
        request_method="POST",
        require_csrf=True,
        permission=Permissions.ADMIN,
    )
    def update_instance_settings(self):
        ai = self.application_instance

        self.application_instance_service.update_application_instance(
            ai,
            developer_key=self.request.params.get("developer_key", "").strip(),
            developer_secret=self.request.params.get("developer_secret", "").strip(),
        )

        for field in ApplicationSettings.fields.values():
            # Notes are updated in the main `info` tab, skip it here
            if field.compound_key == "hypothesis.notes":
                continue

            value = self.request.params.get(field.compound_key)
            value = value.strip() if value else None

            if field.format is asbool:
                value = value == "on"
                ai.settings.set(field.group, field.key, value)

            elif field.format == JSONSetting.AES_SECRET:
                if not value:
                    continue

                ai.settings.set_secret(self._aes_service, field.group, field.key, value)

            else:
                assert field.format is str  # noqa: S101
                ai.settings.set(field.group, field.key, value)

        self.request.session.flash(
            f"Updated application instance settings for {ai.id}", "messages"
        )

        return self._redirect("admin.instance.section", id_=ai.id, section="settings")
