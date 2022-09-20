import base64
from enum import Enum
from functools import lru_cache, partial
from typing import Callable, List, NamedTuple, Optional

from pyramid.request import Request
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


class DeniedWithValidationError(Denied):
    """A denial of an action due to a validation error."""

    def __init__(self, validation_error: ValidationError):
        super().__init__()
        self.validation_error = validation_error


class Identity(NamedTuple):
    userid: str
    permissions: List[str]
    lti_user: Optional[LTIUser] = None


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

    if path in {"/lti_launches", "/content_item_selection", "/api/gateway/h/lti"}:
        return LTIUserSecurityPolicy(get_lti_user_from_launch_params)

    return LTIUserSecurityPolicy(get_lti_user)


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


class LTIUserSecurityPolicy:
    """Security policy based on the information of an LTIUser."""

    def __init__(self, get_lti_user_: Callable[[Request], LTIUser]):
        self._get_lti_user = get_lti_user_

    @staticmethod
    def _get_userid(lti_user):
        # urlsafe_b64encode() requires bytes, so encode the userid to bytes.
        user_id_bytes = lti_user.user_id.encode()

        safe_user_id_bytes = base64.urlsafe_b64encode(user_id_bytes)

        # urlsafe_b64encode() returns ASCII bytes but we need unicode, so
        # decode it.
        safe_user_id = safe_user_id_bytes.decode("ascii")

        return ":".join([safe_user_id, str(lti_user.application_instance_id)])

    def authenticated_userid(self, request):
        identity = self.identity(request)
        if identity is None or not identity.userid:
            return None

        return identity.userid

    def identity(self, request):
        try:
            lti_user = self._get_lti_user(request)
        except ValidationError:
            return Identity("", [])

        if lti_user is None:
            return Identity("", [])

        permissions = [Permissions.LTI_LAUNCH_ASSIGNMENT, Permissions.API]

        if any(
            role in lti_user.roles.lower()
            for role in ["administrator", "instructor", "teachingassistant"]
        ):
            permissions.append(Permissions.LTI_CONFIGURE_ASSIGNMENT)

        return Identity(self._get_userid(lti_user), permissions, lti_user)

    def permits(self, request, _context, permission):
        try:
            # Getting lti_use here again for the potential exception
            # side effect and allow us to return DeniedWithValidationError accordingly
            self._get_lti_user(request)
        except ValidationError as err:
            return DeniedWithValidationError(err)

        return _permits(self.identity(request), permission)

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

    def permits(self, request, _context, permission):
        return _permits(self.identity(request), permission)


def _permits(identity, permission):
    if identity and permission in identity.permissions:
        return Allowed("allowed")

    return Denied("denied")


@lru_cache(maxsize=1)
def get_lti_user_from_launch_params(request) -> LTIUser:
    if "id_token" in request.params:
        return LTI13AuthSchema(request).lti_user()

    return LTI11AuthSchema(request).lti_user()


@lru_cache(maxsize=1)
def get_lti_user(request, from_identity=False) -> Optional[LTIUser]:
    """
    Return a models.LTIUser for the authenticated LTI user.

    Get the authenticated user from one of our LTI bearer tokens.

    If the request doesn't contain a valid bearer token then return None.

    :param request: Current request.
    :param from_identity: Use the lti_user from request.identity.
        Defaults to False to avoid a circular dependency and allow
        security policies to use this function.

    :rtype: models.LTIUser
    """
    lti_user = None
    if from_identity and request.identity and request.identity.lti_user:
        lti_user = request.identity.lti_user
    else:

        bearer_token_schema = BearerTokenSchema(request)
        schemas = [
            partial(bearer_token_schema.lti_user, location="headers"),
            partial(bearer_token_schema.lti_user, location="querystring"),
            partial(bearer_token_schema.lti_user, location="form"),
            OAuthCallbackSchema(request).lti_user,
        ]
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
    config.add_request_method(
        partial(get_lti_user, from_identity=True),
        name="lti_user",
        property=True,
        reify=True,
    )
    config.add_request_method(_get_user, name="user", property=True, reify=True)
