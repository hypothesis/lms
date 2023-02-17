from pyramid.view import view_config
from lms.security import Permissions
from lms.resources._js_config.file_picker_config import FilePickerConfig
from lms.validation._base import PyramidRequestSchema
from marshmallow import Schema

from webargs import fields


class APISyncSchema(PyramidRequestSchema):
    class LMS(Schema):
        product = fields.Str(required=True)

    lms = fields.Nested(LMS, required=True)


@view_config(
    request_method="POST",
    permission=Permissions.API,
    renderer="json",
    route_name="api.assignment.config",
    schema=APISyncSchema,
)
def config(_context, request):
    """Get any config needed to get edit an assignment from the frontend"""
    assignment_id = request.matchdict["assignment_id"]
    assignment = request.find_service(name="assignment").get_by_id(assignment_id)

    application_instance = request.find_service(
        name="application_instance"
    ).get_current()

    args = request, application_instance

    return {
        # Info about the assignments current configuration
        "assignment": {
            "id": assignment.id,
            "group_set_id": assignment.extra["group_set_id"],
            "document": {
                "url": assignment.document_url,
            },
        },
        # Data needed to re-configre it
        "filePicker": {
            "blackboard": FilePickerConfig.blackboard_config(*args),
            "d2l": FilePickerConfig.d2l_config(*args),
            "canvas": FilePickerConfig.canvas_config(*args),
            "google": FilePickerConfig.google_files_config(*args),
            "microsoftOneDrive": FilePickerConfig.microsoft_onedrive(*args),
            "vitalSource": FilePickerConfig.vitalsource_config(*args),
            "jstor": FilePickerConfig.jstor_config(*args),
        },
    }
