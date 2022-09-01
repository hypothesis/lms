import base64
from enum import Enum
from functools import lru_cache, partial
from typing import List, NamedTuple

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


class Identity(NamedTuple):
    userid: str
    permissions: List[str]


class Permissions(Enum):
    LTI_LAUNCH_ASSIGNMENT = "lti_launch_assignment"
    LTI_CONFIGURE_ASSIGNMENT = "lti_configure_assignment"
    API = "api"
    ADMIN = "admin"


@lru_cache(maxsize=1)
def get_policy(request):
    """Pick the right policy based the request's path."""
    path = request.path

    if path.startswith("/admin") or path.startswith("/googleauth"):
        return LMSGoogleSecurityPolicy()

    return LTISecurityPolicy()


class SecurityPolicy:
    """Top-level authentication policy that delegates to sub-policies."""

    def authenticated_userid(self, request):
        return get_policy(request).authenticated_userid(request)

    def identity(self, request):
        return get_policy(request).identity(request)

    def permits(self, request, context, permission):
        return get_policy(request).permits(request, context, permission)

    def remember(self, request, userid, **kw):
        return get_policy(request).remember(request, userid, **kw)

    def forget(self, request):
        return get_policy(request).forget(request)


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
            permissions = [Permissions.LTI_LAUNCH_ASSIGNMENT, Permissions.API]

            if any(
                role in request.lti_user.roles.lower()
                for role in ["administrator", "instructor", "teachingassistant"]
            ):
                permissions.append(Permissions.LTI_CONFIGURE_ASSIGNMENT)

            return Identity(userid, permissions)

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
        request.find_service(UserService).upsert_user(lti_user)

    return lti_user


def _get_user(request):
    return request.find_service(UserService).get(
        request.find_service(name="application_instance").get_current(),
        request.lti_user.user_id,
    )


def includeme(config):
    config.set_security_policy(SecurityPolicy())
    config.add_request_method(_get_lti_user, name="lti_user", property=True, reify=True)
    config.add_request_method(_get_user, name="user", property=True, reify=True)
