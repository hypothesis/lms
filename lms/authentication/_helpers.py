from lms.validation import LaunchParamsSchema, BearerTokenSchema, ValidationError


def get_lti_user(request):
    """
    Return an :class:`~lms.values.LTIUser` for the authenticated LTI user.

    Get the authenticated user from the validated LTI launch params or, failing
    that, from one of our LTI bearer tokens (also validated).

    If the request doesn't contain either valid LTI launch params or a valid
    bearer token then return ``None``.

    :rtype: lms.values.LTIUser
    """
    try:
        return LaunchParamsSchema(request).lti_user()
    except ValidationError:
        pass

    try:
        return BearerTokenSchema(request).lti_user()
    except ValidationError:
        return None


def includeme(config):
    config.add_request_method(get_lti_user, name="lti_user", property=True, reify=True)
