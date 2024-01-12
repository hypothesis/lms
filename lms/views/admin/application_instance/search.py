from marshmallow import validate
from pyramid.view import view_config, view_defaults
from webargs import fields

from lms.models import ApplicationSettings, InvalidOrganizationPublicId
from lms.models.json_settings import JSONSetting
from lms.security import Permissions
from lms.validation import PyramidRequestSchema
from lms.views.admin import flash_validation
from lms.views.admin._schemas import EmptyStringInt
from lms.views.admin.application_instance._core import BaseApplicationInstanceView

SETTINGS_BY_FIELD = {
    field.compound_key: field
    for field in ApplicationSettings.fields
    if field.format != JSONSetting.AES_SECRET
}


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
    organization_public_id = fields.Str(required=False)
    settings_key = fields.Str(required=False)
    settings_value = fields.Str(required=False)


@view_defaults(
    route_name="admin.instance.search",
    renderer="lms:templates/admin/application_instance/search.html.jinja2",
    permission=Permissions.STAFF,
)
class SearchApplicationInstanceViews(BaseApplicationInstanceView):
    @view_config(request_method="GET")
    def search_start(self):
        return {"settings": SETTINGS_BY_FIELD}

    @view_config(request_method="POST", require_csrf=True)
    def search_callback(self):
        if flash_validation(self.request, SearchApplicationInstanceSchema):
            return {"settings": SETTINGS_BY_FIELD}

        settings = None
        if settings_key := self.request.params.get("settings_key"):
            if settings_value := self.request.params.get("settings_value"):
                settings_value = SETTINGS_BY_FIELD.get(settings_key).format(
                    settings_value
                )
            else:
                settings_value = ...

            settings = {settings_key: settings_value}

        try:
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
                organization_public_id=self.request.params.get(
                    "organization_public_id"
                ),
                settings=settings,
            )

        except InvalidOrganizationPublicId as err:
            self.request.session.flash(
                {"organization_public_id": [str(err)]}, "validation"
            )
            return {"settings": SETTINGS_BY_FIELD}

        # Get out the settings key to focus on if it's been searched for
        settings_focus = None
        if settings_key:
            settings_group, settings_subkey = settings_key.split(".")
            settings_focus = SETTINGS_BY_FIELD[settings_key]

            instances = list(instances)  # Ensure we don't consume the generator
            for instance in instances:
                instance.settings_focus_value = instance.settings.get(
                    settings_group, settings_subkey
                )

        return {
            "instances": instances,
            "settings": SETTINGS_BY_FIELD,
            "settings_focus": settings_focus,
        }
