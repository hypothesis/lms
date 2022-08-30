import base64
from enum import Enum
from functools import lru_cache, partial
from typing import List, NamedTuple, Optional, Tuple
from urllib.parse import urljoin, urlparse

from pyramid.security import Allowed, Denied
from pyramid_googleauth import GoogleSecurityPolicy

from lms.models import LTIUser
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
    denied_reason: Optional[ValidationError] = None
    lti_user: Optional[LTIUser] = None


class DeniedWithReason(Denied):
    def __init__(self, reason: ValidationError):
        self.reason = reason
        super().__init__()


class Permissions(Enum):
    LTI_LAUNCH_ASSIGNMENT = "lti_launch_assignment"
    LTI_CONFIGURE_ASSIGNMENT = "lti_configure_assignment"
    API = "api"
    ADMIN = "admin"


class SecurityPolicy:
    """Top-level authentication policy that delegates to sub-policies."""

    def __init__(self):
        self._subpolicies = [LTIUserSecurityPolicy(), LMSGoogleSecurityPolicy()]

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
        route_policy_mapping = {
            request.route_url("content_item_selection"): LTILaunchesSecurityPolicy,
            request.route_url("lti_launches"): LTILaunchesSecurityPolicy,
        }

        # Current URL without query parameters
        url = urljoin(request.url, urlparse(request.url).path)
        if policy := route_policy_mapping.get(url):
            # Found a specific policy we want to apply based on the URL
            return policy()

        for policy in self._subpolicies:
            if policy.authenticated_userid(request):
                # Pick the first policy that returns an user
                return policy

        return self._subpolicies[-1]


class LTIUserSecurityPolicy:
    """
    Security policy which tries all the locations where a LTIUser can be located.

    Check `_get_lti_user` below.
    """

    @classmethod
    def authenticated_userid(cls, request):
        lti_user = _get_lti_user(request, from_identity=False)

        return cls._get_userid_from_lti_user(lti_user)

    def identity(self, request):
        lti_user = _get_lti_user(request, from_identity=False)

        return self._get_identity_from_lti_user(lti_user)

    def permits(self, request, context, permission):
        return _permits(self, request, context, permission)

    def remember(self, request, userid, **kw):
        pass

    def forget(self, request):
        pass

    @staticmethod
    def _get_userid_from_lti_user(lti_user):
        if not lti_user:
            return None
        # urlsafe_b64encode() requires bytes, so encode the userid to bytes.
        user_id_bytes = lti_user.user_id.encode()

        safe_user_id_bytes = base64.urlsafe_b64encode(user_id_bytes)

        # urlsafe_b64encode() returns ASCII bytes but we need unicode, so
        # decode it.
        safe_user_id = safe_user_id_bytes.decode("ascii")

        return ":".join([safe_user_id, str(lti_user.application_instance_id)])

    @classmethod
    def _get_identity_from_lti_user(cls, lti_user):
        userid = cls._get_userid_from_lti_user(lti_user)
        if userid:
            permissions = [Permissions.LTI_LAUNCH_ASSIGNMENT, Permissions.API]

            if any(
                role in lti_user.roles.lower()
                for role in ["administrator", "instructor", "teachingassistant"]
            ):
                permissions.append(Permissions.LTI_CONFIGURE_ASSIGNMENT)

            return Identity(userid, permissions, lti_user=lti_user)

        return Identity("", [])


class LTILaunchesSecurityPolicy(LTIUserSecurityPolicy):
    """
    Security policy for LTI launches.

    No need to use `_get_lti_user` different locations for authentication.
    We'll only look at the locations where LTI 1.1 & 1.3 authentication parameters are located.
    """

    @classmethod
    def authenticated_userid(cls, request):
        lti_user, validation_error = cls._lti_user(request)
        if validation_error:
            return None

        return cls._get_userid_from_lti_user(lti_user)

    def identity(self, request):
        lti_user, validation_error = self._lti_user(request)
        if validation_error:
            return Identity("", [], denied_reason=validation_error)

        return self._get_identity_from_lti_user(lti_user)

    @staticmethod
    @lru_cache
    def _lti_user(request) -> Tuple[Optional[LTIUser], Optional[ValidationError]]:
        """
        Get a `LTIUser` from request using only the relevant LTI schemas.

        Returns a tuple of LTIUser,ValidationError instead of raising the later to:
            - Make the `lru_cache` effective when an exception happens
            - Make the exception value easier to consume for the callers
        """
        schema = LTI11AuthSchema(request).lti_user
        if "id_token" in request.params:
            schema = LTI13AuthSchema(request).lti_user

        try:
            return schema(), None
        except ValidationError as error:
            return None, error


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

    if identity and identity.denied_reason:
        return DeniedWithReason(identity.denied_reason)

    return Denied("denied")


def _get_lti_user(request, from_identity=True):
    """
    Return a models.LTIUser for the authenticated LTI user.

    Get the authenticated user from the validated LTI launch params or, failing
    that, from one of our LTI bearer tokens (also validated).

    If the request doesn't contain either valid LTI launch params or a valid
    bearer token then return ``None``.

    :param: from_identity In case we are using this function directly on a security policy
    use `False` to avoid a recursive call between them.

    :rtype: models.LTIUser
    """

    # We might have already built an LTIUser in a security policy
    if from_identity and request.identity and request.identity.lti_user:
        request.find_service(UserService).upsert_user(request.identity.lti_user)
        return request.identity.lti_user

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
