"""Helpers for configuring the front-end JavaScript application."""

from lms.values import HUser

__all__ = ("configure_grading",)


def configure_grading(request, js_config):
    """
    Insert any needed JS context to configure the front end for grading.

    Note that this is entirely distinct from Canvas Speedgrader, which provides
    its own UI.
    """

    if (
        not request.lti_user.is_instructor
        or not lis_result_sourcedid_svc.is_assignment_gradable(request)
        or request.params.get("tool_consumer_info_product_family_code") == "canvas"
    ):
        return

    js_config["lmsGrader"] = True

    js_config["grading"] = {
        "courseName": request.params.get("context_title"),
        "assignmentName": request.params.get("resource_link_title"),
        "students": [
            {
                "userid": h_user.userid,
                "displayName": h_user.display_name,
                "LISResultSourcedId": student.lis_result_sourcedid,
                "LISOutcomeServiceUrl": student.lis_outcome_service_url,
            }
            for student, h_user in _students_for_assignment(
                context_id=request.params.get("context_id"),
                resource_link_id=request.params.get("resource_link_id"),
                request=request,
            )
        ],
    }


def _students_for_assignment(context_id, resource_link_id, request):
    service = request.find_service(name="lis_result_sourcedid")

    for student in service.fetch_students_by_assignment(
        oauth_consumer_key=request.lti_user.oauth_consumer_key,
        context_id=context_id,
        resource_link_id=resource_link_id,
    ):
        yield student, HUser(
            authority=request.registry.settings["h_authority"],
            username=student.h_username,
            display_name=student.h_display_name,
        )
