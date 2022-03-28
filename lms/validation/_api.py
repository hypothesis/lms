"""Schema for JSON APIs exposed to the frontend."""

import marshmallow
from marshmallow import INCLUDE, Schema, ValidationError, validates_schema
from webargs import fields

from lms.validation._base import JSONPyramidRequestSchema, PyramidRequestSchema


class APIRecordSpeedgraderSchema(JSONPyramidRequestSchema):
    """Schema for validating Canvas Speedgrader submissions from the front end."""

    document_url = fields.Str()
    """URL of the document for this assignment."""

    canvas_file_id = fields.Str()
    """ID of the Canvas file for this assignment."""

    vitalsource_book_id = fields.Str()
    """ID of the VitalSource book for this assignment."""

    vitalsource_cfi = fields.Str()
    """CFI of the VitalSource book for this assignment."""

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

    resource_link_id = fields.Str(required=False, allow_none=True)
    """Canvas doesn't seen the right value on speed grader launches
    so we keep track of the correct one ourselves"""

    ext_lti_assignment_id = fields.Str(required=False, allow_none=True)
    """Canvas doesn't send this value on speed grader launches"""


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

    location = "form"

    document_url = fields.Str(required=True)
    """URL of the target document"""

    context_id = fields.Str(required=True)
    """Course ID for the assignment"""

    context_title = fields.Str(required=True)
    """Course title for the course the assignment belongs to"""

    resource_link_id = fields.Str(required=True)
    """ID of the assignment on the LMS"""

    group_set = fields.Str(required=False, allow_none=True)
    """Groupset the assignment belongs to if created as a smalls groups assignment"""


class APIBlackboardSyncSchema(PyramidRequestSchema):
    class LMS(Schema):
        tool_consumer_instance_guid = fields.Str(required=True)

    class Course(Schema):
        context_id = fields.Str(required=True)

    class Assignment(Schema):
        resource_link_id = fields.Str(required=True)

    class GroupInfo(Schema):
        class Meta:
            unknown = INCLUDE

    lms = fields.Nested(LMS, required=True)
    course = fields.Nested(Course, required=True)
    assignment = fields.Nested(Assignment, required=True)
    group_info = fields.Nested(GroupInfo, required=True)

    gradingStudentId = fields.Str(required=False, allow_none=True)
