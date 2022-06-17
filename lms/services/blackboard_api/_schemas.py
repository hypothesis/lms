"""
Schemas for Blackboard API responses.

See: https://developer.blackboard.com/portal/displayApi
"""
from marshmallow import EXCLUDE, Schema, fields, post_load
from marshmallow.validate import OneOf

from lms.validation._base import RequestsResponseSchema


class BlackboardListFilesSchema(RequestsResponseSchema):
    """Schema for Blackboard API /courses/{courseId}/resources responses."""

    class FileSchema(Schema):
        """Schema for individual Blackboard file dicts."""

        class Meta:
            unknown = EXCLUDE

        id = fields.Str(required=True)
        name = fields.Str(required=True)
        modified = fields.Str(required=True)
        type = fields.Str(required=True)
        mimeType = fields.Str()
        size = fields.Integer()
        parentId = fields.Str()

    results = fields.List(fields.Nested(FileSchema), required=True)

    @post_load
    def post_load(self, data, **_kwargs):
        return data["results"]


class BlackboardPublicURLSchema(RequestsResponseSchema):
    """Schema for Blackboard /courses/{courseId}/resources/{resourceId} responses."""

    downloadUrl = fields.Str(required=True)

    @post_load
    def post_load(self, data, **_kwargs):
        return data["downloadUrl"]


class BlackboardListGroupSetsSchema(RequestsResponseSchema):
    class GroupSetSchema(Schema):
        class Meta:
            unknown = EXCLUDE

        id = fields.Str(required=True)
        name = fields.Str(required=True)

    results = fields.List(fields.Nested(GroupSetSchema), required=True)

    @post_load
    def post_load(self, data, **_kwargs):
        return data["results"]


class BlackboardListGroups(RequestsResponseSchema):
    class GroupSchema(Schema):
        class Meta:
            unknown = EXCLUDE

        class EnrollmentSchema(Schema):
            class Meta:
                unknown = EXCLUDE

            type = fields.Str(
                validate=OneOf(["InstructorOnly", "SelfEnrollment"]), required=True
            )

        id = fields.Str(required=True)
        name = fields.Str(required=True)
        groupSetId = fields.Str(required=False, allow_none=True)
        enrollment = fields.Nested(EnrollmentSchema, required=True)

    results = fields.List(fields.Nested(GroupSchema), required=True)

    @post_load
    def post_load(self, data, **_kwargs):
        return data["results"]
