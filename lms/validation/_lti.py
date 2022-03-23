import marshmallow
from marshmallow.validate import OneOf
from webargs import fields

from lms.validation._base import PyramidRequestSchema


class LTIAuthParamsSchema(marshmallow.Schema):
    class Meta:
        unknown = marshmallow.EXCLUDE

    user_id = marshmallow.fields.Str(required=True)
    roles = marshmallow.fields.Str(required=True)
    tool_consumer_instance_guid = marshmallow.fields.Str(required=True)
    lis_person_name_given = marshmallow.fields.Str(load_default="")
    lis_person_name_family = marshmallow.fields.Str(load_default="")
    lis_person_name_full = marshmallow.fields.Str(load_default="")
    lis_person_contact_email_primary = marshmallow.fields.Str(load_default="")


class CommonLTILaunchSchema(LTIAuthParamsSchema):
    """Fields common to different types of LTI launches."""

    context_id = fields.Str(required=True)
    context_title = fields.Str(required=True)
    lti_version = fields.Str(validate=OneOf(["LTI-1p0", "1.3.0"]), required=True)

    custom_canvas_api_domain = fields.Str()
    custom_canvas_course_id = fields.Str()
    launch_presentation_return_url = fields.Str()
    tool_consumer_info_product_family_code = fields.Str()


class LTI11BasicLTILaunchSchema(CommonLTILaunchSchema):
    lti_message_type = fields.Str(
        validate=OneOf(["basic-lti-launch-request", "LtiResourceLinkRequest"]),
        required=True,
    )
    resource_link_id = fields.Str(required=True)


class OIDCRequestSchema(PyramidRequestSchema):
    location = "form"

    iss = fields.Str(required=True)
    client_id = fields.Str(required=True)

    target_link_uri = fields.Str(required=True)
    login_hint = fields.Str(required=True)
    lti_message_hint = fields.Str(required=True)
