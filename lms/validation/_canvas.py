"""Schemas for Canvas API responses."""
from webargs import fields

from lms.validation.base import RequestsResponseSchema

__all__ = ["CanvasListFilesResponseSchema", "CanvasPublicURLResponseSchema"]


class CanvasListFilesResponseSchema(RequestsResponseSchema):
    """
    Schema for the Canvas API's list_files responses.

    https://canvas.instructure.com/doc/api/files.html#method.files.api_index
    """

    many = True

    display_name = fields.Str(required=True)
    id = fields.Integer(required=True)
    updated_at = fields.String(required=True)


class CanvasPublicURLResponseSchema(RequestsResponseSchema):
    """
    Schema for the Canvas API's public_url responses.

    https://canvas.instructure.com/doc/api/files.html#method.files.public_url
    """

    public_url = fields.Str(required=True)
