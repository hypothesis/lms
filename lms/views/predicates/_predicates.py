def get_url_configured_param(_context, request):
    # The 'url' is a deep linked launch reading the param we sent to the LMS
    # to store during deep linking. All other params are situation specific.
    for param in ["url", "canvas_file", "vitalsource_book"]:
        if param in request.params:
            return param

    return None


def is_db_configured(context, request):
    """Get if this launch has assignment configuration in the DB."""

    return _has_assignment_in_db(context, request, context.resource_link_id)


class ResourceLinkParam:
    COPIED_BRIGHTSPACE = "ext_d2l_resource_link_id_history"
    COPIED_BLACKBOARD = "resource_link_id_history"


def is_brightspace_copied(context, request):
    """Get if this is a Brightspace course we can copy."""

    return not is_db_configured(context, request) and _has_assignment_in_db(
        context, request, request.params.get(ResourceLinkParam.COPIED_BRIGHTSPACE)
    )


def is_blackboard_copied(context, request):
    """Get if this is a Blackboard course we can copy."""

    return not is_db_configured(context, request) and _has_assignment_in_db(
        context, request, request.params.get(ResourceLinkParam.COPIED_BLACKBOARD)
    )


def is_configured(context, request):
    """Get if this launch is configured in any way."""

    for predicate in (
        get_url_configured_param,
        is_db_configured,
        is_blackboard_copied,
        is_brightspace_copied,
    ):
        if predicate(context, request):
            return True

    return False


def is_authorized_to_configure_assignments(_context, request):
    """Get if the current user allowed to configured assignments."""

    if not request.lti_user:
        return False

    roles = request.lti_user.roles.lower()

    return any(
        role in roles for role in ["administrator", "instructor", "teachingassistant"]
    )


def _has_assignment_in_db(context, request, resource_link_id):
    """Get if this launch has an assignment matching."""

    return request.find_service(name="assignment").assignment_exists(
        tool_consumer_instance_guid=context.lti_params.get(
            "tool_consumer_instance_guid"
        ),
        resource_link_id=resource_link_id,
    )
