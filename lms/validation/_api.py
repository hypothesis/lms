"""Schema for JSON APIs exposed to the frontend."""

import marshmallow
from marshmallow import Schema, ValidationError, validates_schema
from webargs import fields

from lms.validation._base import JSONPyramidRequestSchema, PyramidRequestSchema

__all__ = ["APIRecordSpeedgraderSchema", "APIReadResultSchema", "APIRecordResultSchema"]


class APIRecordSpeedgraderSchema(JSONPyramidRequestSchema):
    """Schema for validating Canvas Speedgrader submissions from the front end."""

    document_url = fields.Str()
    """URL of the document for this assignment."""

    canvas_file_id = fields.Str()
    """ID of the Canvas file for this assignment."""

    h_username = fields.Str(required=True)
    """h username generated for the active user."""

    learner_canvas_user_id = fields.Str(required=True)
    """Canvas user ID of the active user."""

    lis_outcome_service_url = fields.Str(required=True)
    """URL provided by the LMS to submit grades or other results to."""

    lis_result_sourcedid = fields.Str(required=True)
    """
    Opaque identifier provided by the LMS to identify a submission. This
    typically encodes the assignment context and LMS user.
    """

    group_set = fields.Int(required=False, allow_none=True)
    """Canvas group_set ID for assignments that use the small groups feature."""


class APIReadResultSchema(PyramidRequestSchema):
    """Schema for validating proxy requests to LTI Outcomes API for reading grades."""

    location = "query"

    lis_outcome_service_url = fields.Str(required=True)
    """URL provided by the LMS to submit grades or other results to."""

    lis_result_sourcedid = fields.Str(required=True)
    """
    Opaque identifier provided by the LMS to identify a submission. This
    typically encodes the assignment context and LMS user.
    """


class APIRecordResultSchema(JSONPyramidRequestSchema):
    """Schema for validating proxy requests to LTI Outcomes API for recording grades."""

    lis_outcome_service_url = fields.Str(required=True)
    """URL provided by the LMS to submit grades or other results to."""

    lis_result_sourcedid = fields.Str(required=True)
    """
    Opaque identifier provided by the LMS to identify a submission. This
    typically encodes the assignment context and LMS user.
    """

    score = fields.Number(
        required=True, validate=marshmallow.validate.Range(min=0, max=1)
    )
    """
    Score — i.e. grade — for this submission. A value between 0 and 1, inclusive.
    """


class APICreateAssignmentSchema(PyramidRequestSchema):
    """Schema for validating assignment creation requests made by our frontend."""

    class Content(Schema):
        class File(Schema):
            display_name = fields.Str(required=True)
            id = fields.Int(required=True)
            updated_at = fields.Str(required=True)
            size = fields.Int(required=True)

        type = fields.Str(
            required=True, validate=marshmallow.validate.OneOf(["url", "file"])
        )
        url = fields.Url(required=False, allow_none=True)
        file = fields.Nested(File, required=False, allow_none=True)

    ext_lti_assignment_id = fields.Str(required=True)
    """Canvas only assignment unique identifier"""

    course_id = fields.Str(required=True)
    """Course ID for the assignment. We'd need it to construct the document_url"""

    groupset = fields.Integer(required=False, allow_none=True)
    """Groupset the assignment belongs to if created as a smalls groups assignment"""

    content = fields.Nested(Content, required=True)

    @validates_schema
    def validate(self, data, **_kwargs):
        if data["content"]["type"] == "url" and not data["content"].get("url"):
            raise ValidationError("url is mandatory with type is 'url'")
        if data["content"]["type"] == "file" and not data["content"].get("file"):
            raise ValidationError("content is mandatory with type is 'file'")
