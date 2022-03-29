"""Validation for the configure_assignment() view."""

from webargs import fields

from lms.validation._lti_launch_params import CommonLTILaunchSchema


class ConfigureAssignmentSchema(CommonLTILaunchSchema):
    """Schema for validating requests to the configure_assignment() view."""

    location = "form"

    document_url = fields.Str(required=True)
    resource_link_id = fields.Str(required=True)
    user_id = fields.Str(required=True)
    context_title = fields.Str(required=True)
    group_set = fields.Str(required=False, allow_none=True)
