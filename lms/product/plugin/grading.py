from typing import List

from lms.models import HUser


class GradingPlugin:
    def configure_grading_for_launch(self, request, js_config, assignment):
        """Configure grading during a launch."""
        if request.lti_user.is_instructor:
            # For instructors, display the toolbar
            students = None
            if assignment.is_gradable:
                students = self._get_students_for_grading(request)

            js_config.enable_instructor_toolbar(
                enable_grading=assignment.is_gradable, student=students
            )
        else:
            # Create or update a record of LIS result data for a student launch
            # We'll query these rows to populate the student dropdown in the
            # instructor toolbar
            request.find_service(name="grading_info").upsert_from_request(request)

    @staticmethod
    def _get_students_for_grading(request) -> List[dict]:
        """Get the available students for grading."""
        grading_info_service = request.find_service(name="grading_info")
        application_instance = request.lti_user.application_instance
        lti_params = request.lti_params
        authority = request.registry.settings["h_authority"]

        # Get one student dict for each student who has launched the assignment
        # and had grading info recorded for them.
        students = []

        grading_infos = grading_info_service.get_by_assignment(
            application_instance=application_instance,
            context_id=lti_params.get("context_id"),
            resource_link_id=lti_params.get("resource_link_id"),
        )

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
                    "userid": h_user.userid(authority),
                    "displayName": h_user.display_name,
                    "lmsId": grading_info.user_id,
                    "LISResultSourcedId": lis_result_sourced_id,
                    # We are using the value from the request instead of the one stored in GradingInfo.
                    # This allows us to still read and submit grades when something in the LMS changes.
                    # For example in LTI version upgrades, the endpoint is likely to change as we move from
                    # LTI 1.1 basic outcomes API to LTI1.3's Assignment and Grade Services.
                    # Also when the install's domain is updated all the records in the DB will be outdated.
                    "LISOutcomeServiceUrl": request.lti_params[
                        "lis_outcome_service_url"
                    ],
                }
            )

        return students
