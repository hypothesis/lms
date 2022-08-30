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


class PathPolicyGetter:
    """Callable that returns different policies based on the request path."""

    def __init__(self, path_policy_mapping):
        """
        Create a new PathPolicyGetter.

        :param path_policy_mapping: Map between route paths and policies
        """
        self.path_policy_mapping = path_policy_mapping

    @lru_cache(maxsize=1)
    def __call__(self, request):
        """Get the corresponding policy based on the request path."""
        for path, policy in self.path_policy_mapping.items():
            # We rely on dict's preserved insertion order
            # and expect that more specific routes are found first.
            if request.path.startswith(path):
                return policy()

        raise ValueError(f"No policy found for {request.path}")


class SecurityPolicy:
    """Top-level authentication policy that delegates to sub-policies."""

    def __init__(self, policy_getter):
        """
        Create a new SecurityPolicy.

        :param policy_getter: Callable that will pick the right policy based on the request object
        """
        self._policy_getter = policy_getter

    def authenticated_userid(self, request):
        return self._policy_getter(request).authenticated_userid(request)

    def identity(self, request):
        return self._policy_getter(request).identity(request)

    def permits(self, request, context, permission):
        return self._policy_getter(request).permits(request, context, permission)

    def remember(self, request, userid, **kw):
        return self._policy_getter(request).remember(request, userid, **kw)

    def forget(self, request):
        return self._policy_getter(request).forget(request)


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
    config.set_security_policy(
        SecurityPolicy(
            PathPolicyGetter(
                path_policy_mapping={
                    # Paths are tested in sequence so the order here
                    # is relevant.
                    # More specific routes should be higher than shorter ones.
                    "/admin": LMSGoogleSecurityPolicy,
                    "/googleauth": LMSGoogleSecurityPolicy,
                    # Fallback for the rest
                    "/": LTISecurityPolicy,
                }
            )
        )
    )
    config.add_request_method(_get_lti_user, name="lti_user", property=True, reify=True)
    config.add_request_method(_get_user, name="user", property=True, reify=True)
