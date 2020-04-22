import hashlib

from pyramid.view import view_config

from lms.models import HGroup, h_group_name


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

    context_id = request.json["course"]["context_id"]
    custom_canvas_course_id = request.json["course"]["custom_canvas_course_id"]
    tool_consumer_instance_guid = request.json["lms"]["tool_consumer_instance_guid"]

    if request.lti_user.is_learner:
        # For learners we only want the client to show the sections that the
        # student belongs to, so fetch only the user's sections.
        sections = canvas_api_svc.authenticated_users_sections(custom_canvas_course_id)
    else:
        # For non-learners (e.g. instructors, teaching assistants) we want the
        # client to show all of the course's sections.
        sections = canvas_api_svc.course_sections(custom_canvas_course_id)

    def group(section):
        """Return an HGroup from the given Canvas section dict."""
        hash_object = hashlib.sha1()
        hash_object.update(tool_consumer_instance_guid.encode())
        hash_object.update(context_id.encode())
        hash_object.update(str(section["id"]).encode())
        authority_provided_id = hash_object.hexdigest()

        return HGroup(h_group_name(section["name"]), authority_provided_id,)

    groups = [group(section) for section in sections]

    lti_h_svc.sync(groups)

    return [group.groupid(authority) for group in groups]
