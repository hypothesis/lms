"""Schema for JSON APIs exposed to the frontend."""

import marshmallow
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
