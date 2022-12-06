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

    def record_result(self, grading_id, score=None, pre_record_hook=None):
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

        :raise TypeError: if the given pre_record_hook returns a non-dict
        """
        raise NotImplementedError()

    def create_lineitem(self, lineitems_url, resource_link_id, label):
        """
        Create a new lineitem associated to one resource_link_id.

        https://www.imsglobal.org/spec/lti-ags/v2p0#container-request-filters
        """
        raise NotImplementedError()
