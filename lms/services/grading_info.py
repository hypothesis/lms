from lms.models import GradingInfo

__all__ = ["GradingInfoService"]


class GradingInfoService:
    """Methods for interacting with GradingInfo records."""

    def __init__(self, _context, request):
        self._db = request.db
        self._lti_user = request.lti_user
        self._authority = request.registry.settings["h_authority"]
        self._application_instance_service = request.find_service(
            name="application_instance"
        )

    def get_by_assignment(self, application_instance, context_id, resource_link_id):
        """
        Return all GradingInfo's for a given assignment.

        The returned list will contain one GradingInfo for each student who has
        launched this assignment (and had GradingInfo data persisted for them).

        :param application_instance: the assignment's application_instance
            (identifies a deployment of our app in an LMS)
        :param context_id: the assignment's context_id
            (identifies the course within the LMS)
        :param resource_link_id: the assignment's resource_link_id
            (identifies the assignment within the LMS course)
        """
        return self._db.query(GradingInfo).filter_by(
            application_instance=application_instance,
            context_id=context_id,
            resource_link_id=resource_link_id,
        )

    def upsert_grading_info(
        self,
        context_id: str,
        resource_link_id: str,
        lis_result_sourcedid=None,
        lis_outcome_service_url=None,
    ):
        """
        Update or create a GradingInfo.

        This function will do nothing if the correct parameters cannot be
        found in the request.
        """

        if not lis_result_sourcedid or not lis_outcome_service_url:
            # This can happen if the user is not a student, or if the needed
            # LIS data is not present on the request.
            return

        application_instance = self._application_instance_service.get_current()

        grading_info = self._find_or_create(
            application_instance=application_instance,
            user_id=self._lti_user.user_id,
            context_id=context_id,
            resource_link_id=resource_link_id,
        )
        grading_info.h_username = self._lti_user.h_user.username
        grading_info.h_display_name = self._lti_user.h_user.display_name

        grading_info.lis_outcome_service_url = lis_outcome_service_url
        grading_info.lis_result_sourcedid = lis_outcome_service_url

    def _find_or_create(self, **query):
        result = self._db.query(GradingInfo).filter_by(**query).one_or_none()

        if result is None:
            result = GradingInfo(**query)
            self._db.add(result)

        return result
