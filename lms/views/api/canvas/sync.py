from pyramid.view import view_config

from lms.models import HGroup


@view_config(
    route_name="canvas_api.sync",
    request_method="POST",
    renderer="json",
    permission="sync_api",
)
def sync(request):
    authority = request.registry.settings["h_authority"]
    canvas_api_svc = request.find_service(name="canvas_api_client")
    lti_h_svc = request.find_service(name="lti_h")

    course_id = request.json["course"]["custom_canvas_course_id"]
    group_info = request.json["group_info"]

    if request.lti_user.is_learner:
        # For learners we only want the client to show the sections that the
        # student belongs to, so fetch only the user's sections.
        sections = canvas_api_svc.authenticated_users_sections(course_id)
    else:
        # For non-learners (e.g. instructors, teaching assistants) we want the
        # client to show all of the course's sections.
        sections = canvas_api_svc.course_sections(course_id)

    tool_consumer_instance_guid = request.json["lms"]["tool_consumer_instance_guid"]
    context_id = request.json["course"]["context_id"]

    def group(section):
        """Return an HGroup from the given Canvas section dict."""

        return HGroup.section_group(
            section_name=section.get("name"),
            tool_consumer_instance_guid=tool_consumer_instance_guid,
            context_id=context_id,
            section_id=section["id"],
        )

    groups = [group(section) for section in sections]
    lti_h_svc.sync(groups, group_info)

    if "learner" in request.json:
        user_id = request.json["learner"]["canvas_user_id"]
        learners_sections = canvas_api_svc.users_sections(user_id, course_id)
        learners_groups = [group(section) for section in learners_sections]
        return [group.groupid(authority) for group in learners_groups]

    return [group.groupid(authority) for group in groups]
