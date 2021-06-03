"""
Schemas for Blackboard API responses.

See: https://developer.blackboard.com/portal/displayApi
"""
from marshmallow import EXCLUDE, Schema, fields, post_load

from lms.validation._base import RequestsResponseSchema


class BlackboardListFilesSchema(RequestsResponseSchema):
    """Schema for Blackboard API /courses/{courseId}/resources responses."""

    class FileSchema(Schema):
        """Schema for an individual file dict inside the "results" list."""

        class Meta:
            unknown = EXCLUDE

        id = fields.Str(required=True)
        display_name = fields.Str(data_key="name", required=True)
        updated_at = fields.Str(data_key="modified", required=True)

    results = fields.List(fields.Nested(FileSchema), required=True)

    @post_load
    def make_object(self, data, **_kwargs):  # pylint:disable=no-self-use
        return data["results"]
