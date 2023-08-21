from lms.models import GradingInfo, HUser

__all__ = ["GradingInfoService"]


class GradingInfoService:
    """Methods for interacting with GradingInfo records."""

    def __init__(self, _context, request):
        self._db = request.db
        self._authority = request.registry.settings["h_authority"]

    def get_students_for_grading(
        self,
        application_instance,
        context_id,
        resource_link_id,
        lis_outcome_service_url,
    ) -> list[dict]:
        """
        Return all students available for grading for a given assignment.

        The returned list will contain one dict for each student who has
        launched this assignment (and had GradingInfo data persisted for them).

        :param application_instance: the assignment's application_instance
            (identifies a deployment of our app in an LMS)
        :param context_id: the assignment's context_id
            (identifies the course within the LMS)
        :param resource_link_id: the assignment's resource_link_id
            (identifies the assignment within the LMS course)
        :param lis_outcome_service_url: Grading URL given by the URL in the current launch
        """
        grading_infos = self._db.query(GradingInfo).filter_by(
            application_instance=application_instance,
            context_id=context_id,
            resource_link_id=resource_link_id,
        )
        students = []

        for grading_info in grading_infos:
            h_user = HUser(
                username=grading_info.h_username,
                display_name=grading_info.h_display_name,
            )

            lis_result_sourced_id = grading_info.lis_result_sourcedid
            if application_instance.lti_version == "1.3.0":
                # In LTI 1.3 lis_result_sourcedid == user_id
                # or rather the concept of lis_result_sourcedid doesn't really exists and the LTI1.3 grading API is based on the user id.
                # We take the user id value instead here for LTI1.3.
                # This is important in the case of upgrades that happen midterm, wih grading_infos from before the upgrade:
                # we might have only the LTI1.1 value for lis_result_sourcedid but if we pick the user id instead
                # we are guaranteed to get the right value for the LTI1.3 API
                lis_result_sourced_id = grading_info.user_id

            students.append(
                {
                    "userid": h_user.userid(self._authority),
                    "displayName": h_user.display_name,
                    "lmsId": grading_info.user_id,
                    "LISResultSourcedId": lis_result_sourced_id,
                    # We are using the value from the request instead of the one stored in GradingInfo.
                    # This allows us to still read and submit grades when something in the LMS changes.
                    # For example in LTI version upgrades, the endpoint is likely to change as we move from
                    # LTI 1.1 basic outcomes API to LTI1.3's Assignment and Grade Services.
                    # Also when the install's domain is updated all the records in the DB will be outdated.
                    "LISOutcomeServiceUrl": lis_outcome_service_url,
                }
            )

        return students

    def upsert(self, lti_user, lis_result_sourcedid, lis_outcome_service_url):
        """
        Update or create a record based on the LTI params found in the request.

        This function will do nothing if the correct parameters cannot be
        found.
        """
        if not lis_result_sourcedid or not lis_outcome_service_url:
            # We're missing something we needed
            # This can happen if the user is not a student, or if the needed
            # LIS data is not present on the request.
            return None

        grading_info = self._find_or_create(
            application_instance=lti_user.application_instance,
            user_id=lti_user.user_id,
            context_id=lti_user.lti.course_id,
            resource_link_id=lti_user.lti.assignment_id,
        )
        grading_info.h_username = lti_user.h_user.username
        grading_info.h_display_name = lti_user.h_user.display_name

        grading_info.lis_outcome_service_url = lis_outcome_service_url
        grading_info.lis_result_sourcedid = lis_result_sourcedid

        return grading_info

    def _find_or_create(self, **query):
        result = self._db.query(GradingInfo).filter_by(**query).one_or_none()

        if result is None:
            result = GradingInfo(**query)
            self._db.add(result)

        return result
