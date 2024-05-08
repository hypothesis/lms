from dataclasses import dataclass


@dataclass
class GradingResult:
    score: float | None
    comment: str | None


class LTIGradingService:  # pragma: no cover
    """
    Service for sending grades back to the LMS.

    Line item:
        A line item is usually a column in the tool platform's gradebook; it is
        able to hold the results associated with a specific activity
        (assignment) for a set of users.

    Line item container:
        A line item container has an array of line items (for a course).

    Result:
        A result is usually a cell in the tool platform's gradebook; it is
        unique for a specific line item and user.

    Score:
        A score represents the last score obtained by the student for the
        tool's activity. It also exposes the current status of the activity
        (like completed or in progress), and status of the grade.

    These are the LTI1.3 concepts, but they have a counter-part in LTI 1.1
    (except for the line item container):

    https://www.imsglobal.org/spec/lti-ags/v2p0#migrating-from-basic-outcomes-service
    """

    def __init__(self, line_item_url: str, line_item_container_url: str | None):
        """
        Initialize the service.

        :param line_item_url: Identifies one line item to read/write grades
            to. In LTI 1.1 this maps to the equivalent
            `lis_outcome_service_url` parameter.
        :param line_item_container_url: Identifies a container that might hold
            many line items
        """
        self.line_item_url = line_item_url
        self.line_item_container_url = line_item_container_url

    def get_score_maximum(self, resource_link_id):  # noqa: ARG002
        """
        Read the grading configuration of an assignment.

        In LTI nomenclature this is reading the line item container.
        :param resource_link_id: ID of the assignment on the LMS.
        """
        return None

    def read_result(self, grading_id) -> GradingResult:
        """
        Return the last-submitted score for a given submission.

        :param grading_id: The submission id
        :return: The score or `None` if no score has been submitted.
        """
        raise NotImplementedError()

    def record_result(self, grading_id, score=None, pre_record_hook=None, comment=None):
        """
        Set the score or content URL for a student submission to an assignment.

        This method also accepts an optional callable hook which will be passed
        the `score` and the `request_body` which it can modify and must return.
        This allows support for extensions (or custom replacements) to the
        standard body.

        :param grading_id: The submission id
        :param score: Float value between 0 and 1.0.
            Defined as required by the LTI spec but is optional in Canvas if
            an `lti_launch_url` is set.
        :param pre_record_hook: Hook to allow modification of the request
        :param comment: Comment to associate with the grade as feedback for the student

        :raise TypeError: if the given pre_record_hook returns a non-dict
        """
        raise NotImplementedError()

    def create_line_item(self, resource_link_id, label):
        """
        Create a new line item associated to one resource_link_id.

        https://www.imsglobal.org/spec/lti-ags/v2p0#container-request-filters
        """
        raise NotImplementedError()
