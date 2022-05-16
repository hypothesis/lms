class LTIGradingService:  # pragma: no cover
    """Service for sending grades back to the LMS."""

    def __init__(self, grading_url):
        self.grading_url = grading_url

    def read_result(self, grading_id):
        """
        Return the last-submitted score for a given submission.

        :param grading_id: The submission id
        :return: The score or `None` if no score has been submitted.
        """
        raise NotImplementedError()

    def record_result(
        self,
        grading_id,
        score=None,
        canvas_lti_launch_url=None,
        canvas_submitted_at=None,
    ):
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
        :param canvas_lti_launch_url:  Launch URL used in Canvas SpeedGrader
            https://erau.instructure.com/doc/api/file.assignment_tools.html

        :param canvas_submitted_at: Indicates when the submission was created.
            This is displayed in the SpeedGrader as the submission date.
            If the submission date matches an existing submission then the existing
            submission is updated rather than creating a new submission.

        :raise TypeError: if the given pre_record_hook returns a non-dict
        """
        raise NotImplementedError()
