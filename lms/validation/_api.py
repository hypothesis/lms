"""Schema for JSON APIs exposed to the frontend."""

from webargs import fields

from lms.validation._helpers import PyramidRequestSchema


__all__ = ["APIRecordSubmissionSchema"]


class APIRecordSubmissionSchema(PyramidRequestSchema):
    """Schema for validating requests from the frontend to record submissions."""

    locations = ["json"]

    document_url = fields.Str()
    """URL of the document for this assignment."""

    canvas_file_id = fields.Str()
    """ID of the Canvas file for this assignment."""

    h_username = fields.Str(required=True)
    """h username generated for the active user."""

    lis_outcome_service_url = fields.Str(required=True)
    """URL provided by the LMS to submit grades or other results to."""

    lis_result_sourcedid = fields.Str(required=True)
    """
    Opaque identifier provided by the LMS to identify a submission. This
    typically encodes the assignment context and LMS user.
    """
