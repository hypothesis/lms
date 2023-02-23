from marshmallow import Schema
from webargs import fields

from lms.validation._base import PyramidRequestSchema


class APIBaseSchema(PyramidRequestSchema):
    """
    Base information originated from an LTI launch.

    We might not need this information in all endpoints but having
    it available just in case simplifies new features and changes.
    """

    class LMS(Schema):
        product = fields.Str(required=True)

    lms = fields.Nested(LMS, required=True)
    resource_link_id = fields.Str(required=True)
    context_id = fields.Str(required=True)
    group_set_id = fields.Str(required=False, allow_none=True)
