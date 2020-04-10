import base64

from lms.validation import ValidationError
from lms.validation.authentication import (
    BearerTokenSchema,
    CanvasOAuthCallbackSchema,
    LaunchParamsAuthSchema,
)

__all__ = ["authenticated_userid", "get_lti_user", "groupfinder"]


def authenticated_userid(lti_user):
    """Return a ``request.authenticated_userid`` string for ``lti_user``."""
    # urlsafe_b64encode() requires bytes, so encode the userid to bytes.
    user_id_bytes = lti_user.user_id.encode()

    safe_user_id_bytes = base64.urlsafe_b64encode(user_id_bytes)

    # urlsafe_b64encode() returns ASCII bytes but we need unicode, so
    # decode it.
    safe_user_id = safe_user_id_bytes.decode("ascii")

    return ":".join([safe_user_id, lti_user.oauth_consumer_key])


def get_lti_user(request):
    """
    Return an models.LTIUser for the authenticated LTI user.

    Get the authenticated user from the validated LTI launch params or, failing
    that, from one of our LTI bearer tokens (also validated).

    If the request doesn't contain either valid LTI launch params or a valid
    bearer token then return ``None``.

    :rtype: models.LTIUser
    """
    try:
        return LaunchParamsAuthSchema(request).lti_user()
    except ValidationError:
        pass

    try:
        return BearerTokenSchema(request).lti_user()
    except ValidationError:
        pass

    try:
        return CanvasOAuthCallbackSchema(request).lti_user()
    except ValidationError:
        return None


def groupfinder(userid, request):
    allowed_groups = list()
    settings = request.registry.settings
    if userid == settings.get("username", None):
        allowed_groups.append("report_viewers")
    return allowed_groups


def includeme(config):
    config.add_request_method(get_lti_user, name="lti_user", property=True, reify=True)
