"""
Schemas for Blackboard API responses.

See: https://developer.blackboard.com/portal/displayApi
"""
from marshmallow import EXCLUDE, Schema, fields, post_load

from lms.validation._base import RequestsResponseSchema


class _FileSchema(Schema):
    """Shared base schema for Blackboard file dicts."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Str(required=True)
    display_name = fields.Str(data_key="name", required=True)
    updated_at = fields.Str(data_key="modified", required=True)
    type = fields.Str(required=True)
    mime_type = fields.Str(data_key="mimeType")

    @post_load
    def post_load(self, data, **_kwargs):  # pylint:disable=no-self-use
        data["id"] = f"blackboard://content-resource/{data['id']}/"
        return data


class BlackboardListFilesSchema(RequestsResponseSchema):
    """Schema for Blackboard API /courses/{courseId}/resources responses."""

    results = fields.List(fields.Nested(_FileSchema), required=True)

    @post_load
    def post_load(self, data, **_kwargs):  # pylint:disable=no-self-use
        pdf_files = []

        for result in data["results"]:
            if (
                result["type"] == "Folder"
                or result.get("mime_type") == "application/pdf"
            ):
                pdf_files.append(result)

                # Delete mime_type: we don't want to send it to the frontend.
                result.pop("mime_type", None)

        return pdf_files


class BlackboardPublicURLSchema(RequestsResponseSchema, _FileSchema):
    """Schema for Blackboard /courses/{courseId}/resources/{resourceId} responses."""

    downloadUrl = fields.Str(required=True)

    @post_load
    def post_load(self, data, **_kwargs):
        return data["downloadUrl"]
