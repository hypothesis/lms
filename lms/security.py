import base64
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache, partial
from typing import Callable, NamedTuple

import sentry_sdk
from pyramid.authentication import AuthTktCookieHelper
from pyramid.request import Request
from pyramid.security import Allowed, Denied
from pyramid_googleauth import GoogleSecurityPolicy

from lms.models import LTIUser
from lms.services import EmailPreferencesService, UserService
from lms.services.email_preferences import InvalidTokenError, UnrecognisedURLError
from lms.validation.authentication import (
    BearerTokenSchema,
    LTI11AuthSchema,
    LTI13AuthSchema,
    OAuthCallbackSchema,
)


class DeniedWithException(Denied):
    """A denial of an action due to an exception."""

    def __init__(self, exception: Exception):
        super().__init__()
        self.exception = exception


class Identity(NamedTuple):
    userid: str
    permissions: list[str]
    lti_user: LTIUser | None = None


class Permissions(Enum):
    LTI_LAUNCH_ASSIGNMENT = "lti_launch_assignment"
    LTI_CONFIGURE_ASSIGNMENT = "lti_configure_assignment"
    API = "api"
    STAFF = "staff"
    ADMIN = "admin"
    GRADE_ASSIGNMENT = "grade_assignment"
    EMAIL_PREFERENCES = "email.preferences"
    DASHBOARD_VIEW = "dashboard.view"


class UnautheticatedSecurityPolicy:  # pragma: no cover
    """Security policy that always returns an unauthenticated user."""

    def authenticated_userid(self, _request):
        return None

    def identity(self, _request):
        return None

    def permits(self, _request, _context, _permission):
        return Denied("")

    def remember(self, _request, _userid, **_kw):
        return []

    def forget(self, _request):
        return []


class SecurityPolicy:
    """Top-level authentication policy that delegates to sub-policies."""

    def authenticated_userid(self, request):
        return self.get_policy(request).authenticated_userid(request)

    def identity(self, request):
        return self.get_policy(request).identity(request)

    def permits(self, request, context, permission):
        return self.get_policy(request).permits(request, context, permission)

    def remember(self, request, userid, **kw):
        return self.get_policy(request).remember(request, userid, **kw)

    def forget(self, request):
        return self.get_policy(request).forget(request)

    @staticmethod
    @lru_cache(maxsize=1)
    def get_policy(request: Request):
        """Pick the right policy based the request's path."""
        # pylint:disable=too-many-return-statements

        path = request.path

        if path.startswith("/admin") or path.startswith("/googleauth"):
            return LMSGoogleSecurityPolicy()

        if path in {"/lti_launches", "/content_item_selection"}:
            # Actual LTI backed authentication
            return LTIUserSecurityPolicy(get_lti_user_from_launch_params)

        if path in {
            "/canvas_oauth_callback",
            "/api/blackboard/oauth/callback",
            "/api/canvas_studio/oauth/callback",
            "/api/d2l/oauth/callback",
        }:
            # LTIUser serialized in the state param for the oauth flow
            return LTIUserSecurityPolicy(get_lti_user_from_oauth_callback)

        # LTUser serialized as query param for authorization failures
        if (path.startswith("/api") and path.endswith("authorize")) or path in {
            # To fetch pages content from LMSes' APIs
            "/api/canvas/pages/proxy",
            "/api/moodle/pages/proxy",
        }:
            return LTIUserSecurityPolicy(
                partial(get_lti_user_from_bearer_token, location="querystring")
            )

        if path.startswith("/api") or path in {
            "/lti/1.3/deep_linking/form_fields",
            "/lti/1.1/deep_linking/form_fields",
            "/lti/reconfigure",
        }:
            # LTUser serialized in the headers for API calls from the frontend
            return LTIUserSecurityPolicy(
                partial(get_lti_user_from_bearer_token, location="headers")
            )

        if path in {"/assignment", "/assignment/edit"} or path.startswith(
            "/dashboard/launch/assignment/"
        ):
            # LTUser serialized in a from for non deep-linked assignment configuration
            return LTIUserSecurityPolicy(
                partial(get_lti_user_from_bearer_token, location="form")
            )

        if path.startswith("/dashboard/assignment/"):
            return LTIUserSecurityPolicy(
                partial(get_lti_user_from_bearer_token, location="cookies")
            )

        if path in {"/email/preferences", "/email/unsubscribe"}:
            return EmailPreferencesSecurityPolicy(
                secret=request.registry.settings["email_preferences_secret"],
                domain=request.domain,
                email_preferences_service=request.find_service(EmailPreferencesService),
                use_secure_cookie=not request.registry.settings["dev"],
            )

        return UnautheticatedSecurityPolicy()


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
        except Exception:  # pylint:disable=broad-exception-caught
            # If anything went wrong, no identity
            return Identity("", [])

        if lti_user is None:
            return Identity("", [])

        permissions = []
        if lti_user.is_learner or lti_user.is_instructor or lti_user.is_admin:
            permissions = [Permissions.LTI_LAUNCH_ASSIGNMENT, Permissions.API]

        if lti_user.is_instructor:
            permissions.append(Permissions.LTI_CONFIGURE_ASSIGNMENT)
            permissions.append(Permissions.GRADE_ASSIGNMENT)
            permissions.append(Permissions.DASHBOARD_VIEW)

        return Identity(self._get_userid(lti_user), permissions, lti_user)

    def permits(self, request, _context, permission):
        try:
            # Getting lti_use here again for the potential exception
            # side effect and allow us to return DeniedWithException accordingly
            self._get_lti_user(request)
        except Exception as err:  # pylint:disable=broad-exception-caught
            return DeniedWithException(err)

        return _permits(self.identity(request), permission)

    def remember(self, request, userid, **kw):
        pass

    def forget(self, request):
        pass


class LMSGoogleSecurityPolicy(GoogleSecurityPolicy):
    def identity(self, request):
        userid = self.authenticated_userid(request)

        if userid and userid.endswith("@hypothes.is"):
            permissions = [Permissions.STAFF]
            if userid in request.registry.settings["admin_users"]:
                permissions.append(Permissions.ADMIN)

            return Identity(userid, permissions=permissions)

        return Identity("", [])

    def permits(self, request, _context, permission):
        return _permits(self.identity(request), permission)


@dataclass
class EmailPreferencesIdentity:
    """The identity class used by EmailPreferencesSecurityPolicy."""

    h_userid: str
    tag: str | None = None


class EmailPreferencesSecurityPolicy:
    """The security policy for the email preferences page."""

    def __init__(
        self,
        secret: str,
        domain: str,
        email_preferences_service: EmailPreferencesService,
        use_secure_cookie: bool,
    ):
        self.cookie = AuthTktCookieHelper(
            secret=secret,
            cookie_name="email.preferences",
            secure=use_secure_cookie,
            timeout=60 * 5,
            reissue_time=0,
            max_age=60 * 5,
            path="/email/preferences",
            http_only=True,
            domain=domain,
        )
        self.email_preferences_service = email_preferences_service

    def identity(self, request):
        try:
            token_payload = self.email_preferences_service.decode(request.url)
        except UnrecognisedURLError:
            pass
        except InvalidTokenError:
            return None
        else:
            return EmailPreferencesIdentity(token_payload.h_userid, token_payload.tag)

        try:
            return EmailPreferencesIdentity(self.cookie.identify(request)["userid"])
        except (KeyError, TypeError):
            return None

    def authenticated_userid(self, request):
        identity = self.identity(request)
        return identity.h_userid if identity else None

    def permits(self, request, _context, permission):
        identity = self.identity(request)

        if identity is not None and permission == Permissions.EMAIL_PREFERENCES:
            return Allowed("Allowed")

        return Denied("Denied")

    def remember(self, request, userid, **_kw):
        return self.cookie.remember(request, userid)


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
def get_lti_user_from_bearer_token(request, location) -> LTIUser:
    return BearerTokenSchema(request).lti_user(location=location)


@lru_cache(maxsize=1)
def get_lti_user_from_oauth_callback(request) -> LTIUser:
    return OAuthCallbackSchema(request).lti_user()


@lru_cache(maxsize=1)
def get_lti_user(request) -> LTIUser | None:
    """
    Return a models.LTIUser for the authenticated LTI user.

    If the request doesn't contain a valid bearer token then return None.

    :param request: Current request.
    """
    lti_user = None
    if request.identity and request.identity.lti_user:
        lti_user = request.identity.lti_user

    if lti_user:
        # Make a record of the user for analytics so we can map from the
        # LTI users and the corresponding user in H
        request.find_service(UserService).upsert_user(lti_user)

        # Attach useful information to sentry in case we get an exception further down the line
        sentry_sdk.set_tag("application_instance_id", lti_user.application_instance_id)

    return lti_user


def _get_user(request):
    return request.find_service(UserService).get(
        request.lti_user.application_instance, request.lti_user.user_id
    )


def includeme(config):
    config.set_security_policy(SecurityPolicy())
    config.add_request_method(get_lti_user, name="lti_user", property=True, reify=True)
    config.add_request_method(_get_user, name="user", property=True, reify=True)
