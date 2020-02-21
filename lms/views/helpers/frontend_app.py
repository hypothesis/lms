"""Helpers for configuring the front-end JavaScript application."""

__all__ = ("configure_grading",)


def configure_grading(request, js_config):
    """
    Insert any needed JS context to configure the front end for grading.

    Note that this is entirely distinct from Canvas Speedgrader, which provides
    its own UI.
    """

    if (
        not request.lti_user.is_instructor
        or not _is_assignment_gradable(request)
        or request.params.get("tool_consumer_info_product_family_code") == "canvas"
    ):
        return

    js_config["lmsGrader"] = True

    grading_infos = request.find_service(name="grading_info").get_by_assignment(
        oauth_consumer_key=request.lti_user.oauth_consumer_key,
        context_id=request.params.get("context_id"),
        resource_link_id=request.params.get("resource_link_id"),
    )

    js_config["grading"] = {
        "courseName": request.params.get("context_title"),
        "assignmentName": request.params.get("resource_link_title"),
        # TODO! - Rename this in the front end?
        "students": [
            {
                "userid": h_user.userid,
                "displayName": h_user.display_name,
                "LISResultSourcedId": grading_info.lis_result_sourcedid,
                "LISOutcomeServiceUrl": grading_info.lis_outcome_service_url,
            }
            for (grading_info, h_user) in grading_infos
        ],
    }


def _is_assignment_gradable(request):
    # When an instructor launches an LTI assignment, Blackboard sets the
    # `lis_outcome_service_url` form param if evaluation is enabled or omits it otherwise.
    #
    # When extending the generic LTI grader to support other LMSes, we may need
    # a different method to detect whether grading is enabled for a given
    # assignment.
    #
    # The URL here is not actually used to submit grades. Instead that URL
    # is passed to us when a _student_ launches the assignment and recorded for
    # use when an instructor launches the assignment.
    return "lis_outcome_service_url" in request.params
