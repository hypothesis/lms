from webargs import fields

from lms.validation._base import PyramidRequestSchema


class OIDCRequestSchema(PyramidRequestSchema):
    location = "form"

    iss = fields.Str(required=True)
    client_id = fields.Str(required=True)

    target_link_uri = fields.Str(required=True)
    login_hint = fields.Str(required=True)
    lti_message_hint = fields.Str(required=True)
