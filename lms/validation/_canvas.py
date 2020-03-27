"""Schemas for Canvas API responses."""
from marshmallow import Schema, fields, post_load, validate

from lms.validation._base import RequestsResponseSchema


class CanvasAuthenticatedUsersSectionsResponseSchema(RequestsResponseSchema):
    """
    Schema for the Canvas API's "authenticated user's sections" responses.

    Canvas doesn't have an "authenticated user's sections" API endpoint as
    such, so we instead call its get course API
    (https://canvas.instructure.com/doc/api/courses.html#method.courses.show)
    with the ?include[]=sections query param and then extract only the part of
    the response that we want (the list of sections with their names and IDs).
    """

    # A private nested schema for validating each individual section dict
    # within the "sections" list in the Canvas API's response.
    class _SectionSchema(Schema):
        id = fields.Int(required=True)
        name = fields.String(required=True)

    sections = fields.List(
        fields.Nested(_SectionSchema), validate=validate.Length(min=1), required=True
    )

    @post_load
    def post_load(self, data, **_kwargs):  # pylint:disable=no-self-use
        # Return the list of section dicts directly (rather than returning
        # the wrapping {"sections": [<list_of_section_dicts>]} dict).
        #
        # If we get as far as this method then data["sections"] is guaranteed
        # to be a list of one-or-more valid section dicts, so we don't need to
        # code defensively here.
        return data["sections"]


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
