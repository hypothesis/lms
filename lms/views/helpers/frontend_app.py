"""Helpers for configuring the front-end JavaScript application."""

from lms.values import HUser

__all__ = ("configure_grading",)


def configure_grading(request, js_config):
    """
    Insert any needed JS context to configure the front end for grading.

    This is only enabled for instructors on BlackBoard for now. Note that this
    is entirely distinct from Canvas Speedgrader, which provides its own UI.
    """
    if request.lti_user.is_instructor and _is_blackboard(request):
        js_config["lmsGrader"] = True

    js_config["grading"] = {}

    lis_result_sourcedid_svc = request.find_service(name="lis_result_sourcedid")
    lis_result_sourcedids = lis_result_sourcedid_svc.fetch_students_by_assignment(
        oauth_consumer_key=request.lti_user.oauth_consumer_key,
        context_id=request.params.get("context_id"),
        resource_link_id=request.params.get("resource_link_id"),
    )
    students = []
    for student in lis_result_sourcedids:
        # Using ``HUser`` NamedTuple to get at the ``userid`` prop
        h_user = HUser(
            authority=request.registry.settings["h_authority"],
            username=student.h_username,
            display_name=student.h_display_name,
        )
        students.append(
            {
                "userid": h_user.userid,
                "displayName": h_user.display_name,
                "LISResultSourcedId": student.lis_result_sourcedid,
                "LISOutcomeServiceUrl": student.lis_outcome_service_url,
            }
        )

    js_config["grading"]["students"] = students


def _is_blackboard(request):
    family_code = request.params.get("tool_consumer_info_product_family_code", "")
    return family_code == "BlackboardLearn"
