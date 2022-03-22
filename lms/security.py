import base64
import warnings
from enum import Enum
from functools import lru_cache, partial
from typing import List, NamedTuple

import jwt
import marshmallow
from pyramid.authentication import AuthTktCookieHelper
from pyramid.security import Allowed, Denied
from pyramid_googleauth import GoogleSecurityPolicy

from lms.services import UserService
from lms.validation import ValidationError
from lms.validation.authentication import (
    BearerTokenSchema,
    LTI11AuthSchema,
    LTI13AuthSchema,
    OAuthCallbackSchema,
)
from lms.validation.authentication._exceptions import InvalidJWTError


class Identity(NamedTuple):
    userid: str
    permissions: List[str]


class Permissions(Enum):
    LTI_LAUNCH_ASSIGNMENT = "lti_launch_assignment"
    REPORTS_VIEW = "report_viewers"
    API = "api"
    ADMIN = "admin"


class SecurityPolicy:
    """Top-level authentication policy that delegates to sub-policies."""

    def __init__(self, lms_secret):
        self._subpolicies = [
            LTISecurityPolicy(),
            AuthTktCookieSecurityPolicy(lms_secret, hashalg="sha512"),
            LMSGoogleSecurityPolicy(),
        ]

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
        for policy in self._subpolicies:
            if policy.authenticated_userid(request):
                return policy

        return self._subpolicies[-1]


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

    def authenticated_userid(self, request):
        identity = self.identity(request)
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

        # urlsafe_b64encode() requires bytes, so encode the userid to bytes.
        user_id_bytes = request.lti_user.user_id.encode()

        safe_user_id_bytes = base64.urlsafe_b64encode(user_id_bytes)

        # urlsafe_b64encode() returns ASCII bytes but we need unicode, so
        # decode it.
        safe_user_id = safe_user_id_bytes.decode("ascii")

        return ":".join([safe_user_id, str(request.lti_user.application_instance_id)])

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


class LMSGoogleSecurityPolicy(GoogleSecurityPolicy):
    def identity(self, request):
        userid = self.authenticated_userid(request)

        if userid and userid.endswith("@hypothes.is"):
            return Identity(userid, permissions=[Permissions.ADMIN])

        return Identity("", [])

    def permits(self, request, context, permission):
        return _permits(self, request, context, permission)


def _permits(policy, request, _context, permission):
    identity = policy.identity(request)
    if identity and permission in identity.permissions:
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
        LTI11AuthSchema(request).lti_user,
        partial(bearer_token_schema.lti_user, location="headers"),
        partial(bearer_token_schema.lti_user, location="querystring"),
        partial(bearer_token_schema.lti_user, location="form"),
        OAuthCallbackSchema(request).lti_user,
    ]
    # Avoid checking for the LTI1.3 JWT if not there
    if "id_token" in request.params:
        # Don't replace all auth methods in case somehow we have a bogus token
        # but try this one first.
        schemas.insert(0, LTI13AuthSchema(request).lti_user)

    lti_user = None
    for schema in schemas:
        try:
            lti_user = schema()
            break
        except ValidationError:
            continue

    if lti_user:
        # Make a record of the user for analytics so we can map from the
        # LTI users and the corresponding user in H
        request.find_service(UserService).store_lti_user(lti_user)

    return lti_user


def _get_user(request):
    return request.find_service(UserService).get(
        request.find_service(name="application_instance").get_current(),
        request.lti_user.user_id,
    )


def _get_lti_jwt(request):
    id_token = request.params.get("id_token")
    if not id_token:
        return {}

    try:
        jwt_params = jwt.decode(id_token, options={"verify_signature": False})
    except InvalidJWTError as err:
        raise marshmallow.ValidationError("Invalid id_token", "authorization") from err

    warnings.warn("Using not verified JWT token")
    return jwt_params


def includeme(config):
    config.set_security_policy(SecurityPolicy(config.registry.settings["lms_secret"]))
    config.add_request_method(_get_lti_user, name="lti_user", property=True, reify=True)
    config.add_request_method(_get_lti_jwt, name="lti_jwt", property=True, reify=True)
    config.add_request_method(_get_user, name="user", property=True, reify=True)
