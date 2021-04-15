import base64
from enum import Enum
from functools import lru_cache, partial
from typing import List, NamedTuple

from pyramid.authentication import AuthTktCookieHelper
from pyramid.security import Allowed, Denied

from lms.validation import ValidationError
from lms.validation.authentication import (
    BearerTokenSchema,
    CanvasOAuthCallbackSchema,
    LaunchParamsAuthSchema,
)


class Identity(NamedTuple):
    userid: str
    permissions: List[str]


class Permissions(Enum):
    LTI_LAUNCH_ASSIGNMENT = "lti_launch_assignment"
    REPORTS_VIEW = "report_viewers"
    API = "api"


class SecurityPolicy:
    """Top-level authentication policy that delegates to sub-policies."""

    def __init__(self, lms_secret):
        self._lti_authentication_policy = LTISecurityPolicy()
        self._auth_tkt_authentication_policy = AuthTktCookieSecurityPolicy(
            lms_secret, hashalg="sha512"
        )

    def authenticated_userid(self, request):
        return self._policy(request).authenticated_userid(request)

    def identity(self, request):
        return self._policy(request).identity(request)

    def permits(self, request, context, permission):
        return self._policy(request).permits(request, context, permission)

    def remember(self, request, userid, **kw):
        return self._policy(request).remember(request, userid, **kw)

    def forget(self, request):
        return self._policy(request).forget(request)

    @lru_cache(maxsize=1)
    def _policy(self, request):
        if self._lti_authentication_policy.authenticated_userid(request):
            return self._lti_authentication_policy

        return self._auth_tkt_authentication_policy


class AuthTktCookieSecurityPolicy:
    def __init__(self, lms_secret, hashalg="sha512"):
        self._helper = AuthTktCookieHelper(lms_secret, hashalg=hashalg)

    def identity(self, request):
        identity = self._helper.identify(request)

        if identity is None:
            return Identity("", [])

        userid = identity["userid"]
        permissions = []
        settings = request.registry.settings
        if userid == settings.get("username", None):
            permissions = [Permissions.REPORTS_VIEW]

        return Identity(userid, permissions)

    @classmethod
    def authenticated_userid(cls, request):
        identity = request.identity
        return identity.userid if identity else None

    def permits(self, request, context, permission):
        return _permits(self, request, context, permission)

    def remember(self, request, userid, **kw):
        return self._helper.remember(request, userid, **kw)

    def forget(self, request):
        return self._helper.forget(request)


class LTISecurityPolicy:
    @classmethod
    def authenticated_userid(cls, request):
        if request.lti_user is None:
            return None

        return _authenticated_userid(request.lti_user)

    def identity(self, request):
        userid = self.authenticated_userid(request)

        if userid:
            return Identity(
                userid, [Permissions.LTI_LAUNCH_ASSIGNMENT, Permissions.API]
            )

        return Identity("", [])

    def permits(self, request, context, permission):
        return _permits(self, request, context, permission)

    def remember(self, request, userid, **kw):
        pass

    def forget(self, request):
        pass


def _authenticated_userid(lti_user):
    """Return a request.authenticated_userid string for lti_user."""
    # urlsafe_b64encode() requires bytes, so encode the userid to bytes.
    user_id_bytes = lti_user.user_id.encode()

    safe_user_id_bytes = base64.urlsafe_b64encode(user_id_bytes)

    # urlsafe_b64encode() returns ASCII bytes but we need unicode, so
    # decode it.
    safe_user_id = safe_user_id_bytes.decode("ascii")

    return ":".join([safe_user_id, lti_user.oauth_consumer_key])


def _permits(policy, request, _context, permission):  # pylint: disable=unused-argument
    if permission in request.identity.permissions:
        return Allowed("allowed")

    return Denied("denied")


def _get_lti_user(request):
    """
    Return a models.LTIUser for the authenticated LTI user.

    Get the authenticated user from the validated LTI launch params or, failing
    that, from one of our LTI bearer tokens (also validated).

    If the request doesn't contain either valid LTI launch params or a valid
    bearer token then return ``None``.

    :rtype: models.LTIUser
    """
    bearer_token_schema = BearerTokenSchema(request)

    schemas = [
        LaunchParamsAuthSchema(request).lti_user,
        partial(bearer_token_schema.lti_user, location="headers"),
        partial(bearer_token_schema.lti_user, location="querystring"),
        partial(bearer_token_schema.lti_user, location="form"),
        CanvasOAuthCallbackSchema(request).lti_user,
    ]

    for schema in schemas:
        try:
            return schema()
        except ValidationError:
            continue

    return None


def includeme(config):
    config.set_security_policy(SecurityPolicy(config.registry.settings["lms_secret"]))
    config.add_request_method(_get_lti_user, name="lti_user", property=True, reify=True)
