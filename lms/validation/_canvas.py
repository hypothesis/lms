"""Schemas for Canvas API responses."""
from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_load,
    validate,
    validates_schema,
)

from lms.validation._base import RequestsResponseSchema


class _SectionSchema(Schema):
    """
    Schema for an individual course section dict.

    These course section dicts appear in various different Canvas API responses.
    This _SectionSchema class is used as a base class or nested schema by
    various schemas below for Canvas API responses that contain section dicts.
    """

    id = fields.Int(required=True)
    name = fields.String(required=True)


class CanvasAuthenticatedUsersSectionsResponseSchema(RequestsResponseSchema):
    """
    Schema for the Canvas API's "authenticated user's sections" responses.

    Canvas doesn't have an "authenticated user's sections" API endpoint as
    such, so we instead call its get course API
    (https://canvas.instructure.com/doc/api/courses.html#method.courses.show)
    with the ?include[]=sections query param and then extract only the part of
    the response that we want (the list of sections with their names and IDs).
    """

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


class CanvasCourseSectionsResponseSchema(RequestsResponseSchema, _SectionSchema):
    """
    Schema for the Canvas API's "list course sections" responses.

    https://canvas.instructure.com/doc/api/sections.html#method.sections.index
    """

    many = True

    @validates_schema(pass_many=True)
    def _validate_length(self, data, **kwargs):  # pylint:disable=no-self-use
        # If we get as far as this method then data is guaranteed to be a list
        # so the only way it can be falsey is if it's an empty list.
        if not data:
            raise ValidationError("Shorter than minimum length 1.")


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
