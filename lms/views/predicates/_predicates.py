from lms.views.lti.basic_launch import ResourceLinkParam


def get_url_configured_param(_context, request):
    """Get the URL param if we are configured by URL alone."""

    # The 'url' is a deep linked launch reading the param we sent to the LMS
    # to store during deep linking. All other params are situation specific.
    for param in ["url", "canvas_file", "vitalsource_book"]:
        if param in request.params:
            return param

    return None


def get_db_configured_param(context, request):
    """Get the URL link id param if we have a matching DB record."""

    param, _assignment = _get_db_configured_param_and_assignment(context, request)

    return param


def _get_db_configured_param_and_assignment(context, request):
    """Get a tuple of param and assignment if we have a matching DB record."""

    for param in (
        ResourceLinkParam.LTI,
        ResourceLinkParam.COPIED_BRIGHTSPACE,
        ResourceLinkParam.COPIED_BLACKBOARD,
    ):
        # Horrible work around
        if param == ResourceLinkParam.LTI:
            resource_link_id = context.resource_link_id
        else:
            resource_link_id = context.lti_params.get(param)

        if not resource_link_id:
            continue

        assigment = request.find_service(name="assignment").get_assignment(
            tool_consumer_instance_guid=context.lti_params.get(
                "tool_consumer_instance_guid"
            ),
            resource_link_id=resource_link_id,
        )
        if assigment:
            return param, assigment

    return None, None


def is_authorized_to_configure_assignments(_context, request):
    """Get if the current user allowed to configured assignments."""

    if not request.lti_user:
        return False

    roles = request.lti_user.roles.lower()

    return any(
        role in roles for role in ["administrator", "instructor", "teachingassistant"]
    )
