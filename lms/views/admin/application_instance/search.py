from marshmallow import validate
from pyramid.view import view_config, view_defaults
from webargs import fields

from lms.security import Permissions
from lms.validation import PyramidRequestSchema
from lms.views.admin import flash_validation
from lms.views.admin._schemas import EmptyStringInt
from lms.views.admin.application_instance.view import (
    APPLICATION_INSTANCE_SETTINGS,
    APPLICATION_INSTANCE_SETTINGS_COLUMNS,
)


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


@view_defaults(
    request_method="GET",
    permission=Permissions.ADMIN,
    route_name="admin.instance.search",
    renderer="lms:templates/admin/application_instance/search.html.jinja2",
)
class SearchApplicationInstanceViews:
    def __init__(self, request):
        self.request = request
        self.application_instance_service = request.find_service(
            name="application_instance"
        )

    @view_config()
    def search_start(self):
        return {"settings": APPLICATION_INSTANCE_SETTINGS_COLUMNS}

    @view_config(request_method="POST", require_csrf=True)
    def search_callback(self):
        if flash_validation(self.request, SearchApplicationInstanceSchema):
            return {}

        settings = None
        if settings_key := self.request.params.get("settings_key"):
            if settings_value := self.request.params.get("settings_value"):
                settings_value = APPLICATION_INSTANCE_SETTINGS.get(
                    tuple(settings_key.split("."))
                )(settings_value)
            else:
                settings_value = ...

            settings = {settings_key: settings_value}

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
            settings=settings,
        )

        return {
            "instances": instances,
            "settings": APPLICATION_INSTANCE_SETTINGS_COLUMNS,
        }
