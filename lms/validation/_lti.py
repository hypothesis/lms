from webargs import fields
import marshmallow
from marshmallow.validate import OneOf

from lms.validation._base import PyramidRequestSchema, Reach


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


class LTI13AuthParamsSchema(LTIAuthParamsSchema):
    class Meta:
        unknown = marshmallow.EXCLUDE

    user_id = marshmallow.fields.Str(required=True, data_key="sub")
    roles = marshmallow.fields.List(
        fields.Str(),
        required=True,
        data_key="https://purl.imsglobal.org/spec/lti/claim/roles",
    )
    tool_consumer_instance_guid = Reach(
        fields.Str(),
        data_key="https://purl.imsglobal.org/spec/lti/claim/tool_platform",
        path="guid",
        required=True,
    )
    lis_person_name_given = marshmallow.fields.Str(
        data_key="given_name", load_default=""
    )
    lis_person_name_family = marshmallow.fields.Str(
        data_key="family_name", load_default=""
    )
    lis_person_name_full = marshmallow.fields.Str(data_key="name", load_default="")
    lis_person_contact_email_primary = marshmallow.fields.Str(
        data_key="email", load_default=""
    )

    issuer = marshmallow.fields.Str(data_key="iss", required=True)
    client_id = marshmallow.fields.Str(data_key="aud", required=True)
    deployment_id = marshmallow.fields.Str(
        data_key="https://purl.imsglobal.org/spec/lti/claim/deployment_id",
        required=True,
    )

    @marshmallow.post_load
    def stringify_roles(self, data, **_kwargs):
        data["roles"] = ",".join(data["roles"])
        return data


class CommonLTILaunchSchema(LTIAuthParamsSchema):
    """Fields common to different types of LTI launches."""

    context_id = fields.Str(required=True)
    context_title = fields.Str(required=True)
    lti_version = fields.Str(validate=OneOf(["LTI-1p0", "1.3.0"]), required=True)

    custom_canvas_api_domain = fields.Str()
    custom_canvas_course_id = fields.Str()
    launch_presentation_return_url = fields.Str()
    tool_consumer_info_product_family_code = fields.Str()


class LTI13CommonLTILaunchSchema(LTI13AuthParamsSchema):
    context_id = Reach(
        fields.Str(),
        data_key="https://purl.imsglobal.org/spec/lti/claim/context",
        path="id",
        required=True,
        load_only=True,
    )
    context_title = Reach(
        fields.Str(),
        data_key="https://purl.imsglobal.org/spec/lti/claim/context",
        path="title",
        required=True,
        load_only=True,
    )

    lti_version = fields.Str(
        validate=OneOf(["1.3.0"]),
        required=True,
        data_key="https://purl.imsglobal.org/spec/lti/claim/version",
    )

    custom_canvas_api_domain = fields.Str()
    custom_canvas_course_id = fields.Str()
    launch_presentation_return_url = fields.Str()

    tool_consumer_info_product_family_code = Reach(
        fields.Str(),
        data_key="https://purl.imsglobal.org/spec/lti/claim/tool_platform",
        path="product_family_code",
        required=True,
        load_only=True,
    )


class LTI11BasicLTILaunchSchema(CommonLTILaunchSchema):
    lti_message_type = fields.Str(
        validate=OneOf(["basic-lti-launch-request", "LtiResourceLinkRequest"]),
        required=True,
    )
    resource_link_id = fields.Str(required=True)


class LTI13BasicLTILaunchSchema(LTI13CommonLTILaunchSchema):
    url = fields.Str(required=False)

    resource_link_id = Reach(
        fields.Str(),
        data_key="https://purl.imsglobal.org/spec/lti/claim/resource_link",
        path="id",
        required=True,
        load_only=True,
    )
    lti_message_type = fields.Str(
        validate=OneOf(["LtiResourceLinkRequest"]),
        required=True,
        data_key="https://purl.imsglobal.org/spec/lti/claim/message_type",
    )


class OIDCRequestSchema(PyramidRequestSchema):
    location = "form"

    iss = fields.Str(required=True)
    client_id = fields.Str(required=True)

    target_link_uri = fields.Str(required=True)
    login_hint = fields.Str(required=True)
    lti_message_hint = fields.Str(required=True)
