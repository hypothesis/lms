from unittest.mock import patch, sentinel

import pytest
from pyramid.interfaces import ISecurityPolicy
from pyramid.security import Allowed, Denied

from lms.security import (
    CookiesBearerTokenLTIUserPolicy,
    DeniedWithException,
    EmailPreferencesIdentity,
    EmailPreferencesSecurityPolicy,
    FormBearerTokenLTIUserPolicy,
    HeadersBearerTokenLTIUserPolicy,
    Identity,
    LaunchParamsLTIUserPolicy,
    LMSGoogleSecurityPolicy,
    LTIUserSecurityPolicy,
    OAuthCallbackLTIUserPolicy,
    Permissions,
    QueryStringBearerTokenLTIUserPolicy,
    SecurityPolicy,
    _get_user,
    get_lti_user,
    includeme,
)
from lms.services.email_preferences import (
    InvalidTokenError,
    TokenPayload,
    UnrecognisedURLError,
)
from lms.validation import ValidationError
from tests import factories


class TestIncludeMe:
    def test_it_sets_security_policy(self, pyramid_config, SecurityPolicy):
        includeme(pyramid_config)

        SecurityPolicy.assert_called_once_with()
        assert (
            pyramid_config.registry.queryUtility(ISecurityPolicy)
            == SecurityPolicy.return_value
        )

    @pytest.fixture(autouse=True)
    def SecurityPolicy(self, patch):
        return patch("lms.security.SecurityPolicy")


class TestLMSGoogleSecurityPolicy:
    @pytest.mark.parametrize(
        "userid,expected_identity",
        [
            (
                "testuser@hypothes.is",
                Identity(
                    userid="testuser@hypothes.is",
                    permissions=[Permissions.STAFF, Permissions.DASHBOARD_VIEW],
                ),
            ),
            (
                "admin@hypothes.is",
                Identity(
                    userid="admin@hypothes.is",
                    permissions=[
                        Permissions.STAFF,
                        Permissions.DASHBOARD_VIEW,
                        Permissions.ADMIN,
                    ],
                ),
            ),
            ("testuser@example.com", None),
        ],
    )
    def test_identity(self, policy, pyramid_request, userid, expected_identity):
        pyramid_request.registry.settings = {"admin_users": ["admin@hypothes.is"]}
        pyramid_request.session["googleauth.userid"] = userid

        assert policy.identity(pyramid_request) == expected_identity

    def test_identity_when_no_user_is_logged_in(self, policy, pyramid_request):
        assert not policy.identity(pyramid_request)

    def test_authenticated_userid(self, policy, pyramid_request):
        pyramid_request.session["googleauth.userid"] = "testuser@hypothes.is"

        assert policy.authenticated_userid(pyramid_request) == "testuser@hypothes.is"

    @pytest.mark.parametrize(
        "permission,expected_result",
        [
            (Permissions.STAFF, Allowed("allowed")),
            ("some-other-permission", Denied("denied")),
        ],
    )
    def test_permits(self, policy, pyramid_request, permission, expected_result):
        pyramid_request.session["googleauth.userid"] = "testuser@hypothes.is"

        assert (
            policy.permits(pyramid_request, sentinel.context, permission)
            == expected_result
        )

    @pytest.fixture
    def policy(self):
        return LMSGoogleSecurityPolicy()


class TestEmailPreferencesSecurityPolicy:
    @pytest.mark.parametrize(
        "method,expected_result",
        [
            ("identity", EmailPreferencesIdentity(sentinel.h_userid, sentinel.tag)),
            ("authenticated_userid", sentinel.h_userid),
        ],
    )
    def test_identity_returns_the_identity_from_the_token(
        self,
        policy,
        pyramid_request,
        email_preferences_service,
        method,
        expected_result,
    ):
        email_preferences_service.decode.return_value = TokenPayload(
            sentinel.h_userid, sentinel.tag
        )

        result = getattr(policy, method)(pyramid_request)

        email_preferences_service.decode.assert_called_once_with(pyramid_request.url)
        assert result == expected_result

    @pytest.mark.parametrize("method", ["identity", "authenticated_userid"])
    def test_identity_returns_None_if_the_token_is_invalid(
        self, policy, pyramid_request, email_preferences_service, method
    ):
        email_preferences_service.decode.side_effect = InvalidTokenError

        assert getattr(policy, method)(pyramid_request) is None

    @pytest.mark.parametrize(
        "method,expected_result",
        [
            ("identity", EmailPreferencesIdentity(sentinel.h_userid)),
            ("authenticated_userid", sentinel.h_userid),
        ],
    )
    def test_identity_returns_the_identity_from_the_cookie(
        self,
        policy,
        pyramid_request,
        email_preferences_service,
        AuthTktCookieHelper,
        method,
        expected_result,
    ):
        email_preferences_service.decode.side_effect = UnrecognisedURLError
        AuthTktCookieHelper.return_value.identify.return_value = {
            "userid": sentinel.h_userid
        }

        result = getattr(policy, method)(pyramid_request)

        AuthTktCookieHelper.return_value.identify.assert_called_once_with(
            pyramid_request
        )
        assert result == expected_result

    @pytest.mark.parametrize("method", ["identity", "authenticated_userid"])
    def test_identity_returns_None_if_theres_no_cookie(
        self,
        policy,
        pyramid_request,
        email_preferences_service,
        AuthTktCookieHelper,
        method,
    ):
        email_preferences_service.decode.side_effect = UnrecognisedURLError
        AuthTktCookieHelper.return_value.identify.return_value = None

        result = getattr(policy, method)(pyramid_request)

        assert result is None

    @pytest.mark.parametrize("method", ["identity", "authenticated_userid"])
    @pytest.mark.parametrize("exception_class", [KeyError, TypeError])
    def test_identity_returns_None_if_the_cookie_is_missing_or_invalid(
        self,
        policy,
        pyramid_request,
        email_preferences_service,
        AuthTktCookieHelper,
        exception_class,
        method,
    ):
        email_preferences_service.decode.side_effect = UnrecognisedURLError
        AuthTktCookieHelper.return_value.identify.side_effect = exception_class

        assert getattr(policy, method)(pyramid_request) is None

    @pytest.mark.parametrize(
        "permission,expected_result",
        [
            (Permissions.EMAIL_PREFERENCES, Allowed("Allowed")),
            ("foo", Denied("Denied")),
        ],
    )
    def test_permits_when_authenticated(
        self, pyramid_request, policy, permission, expected_result
    ):
        result = policy.permits(pyramid_request, sentinel.context, permission)

        assert result == expected_result

    @pytest.mark.parametrize(
        "permission,expected_result",
        [(Permissions.EMAIL_PREFERENCES, Denied("Denied")), ("foo", Denied("Denied"))],
    )
    def test_permits_when_not_authenticated(
        self,
        pyramid_request,
        policy,
        permission,
        expected_result,
        email_preferences_service,
    ):
        email_preferences_service.decode.side_effect = InvalidTokenError

        result = policy.permits(pyramid_request, sentinel.context, permission)

        assert result == expected_result

    def test_remember(self, policy, pyramid_request, AuthTktCookieHelper):
        result = policy.remember(pyramid_request, sentinel.userid)

        AuthTktCookieHelper.return_value.remember.assert_called_once_with(
            pyramid_request, sentinel.userid
        )
        assert result == AuthTktCookieHelper.return_value.remember.return_value

    @pytest.fixture
    def policy(self, email_preferences_service):
        return EmailPreferencesSecurityPolicy(
            secret="test_email_preferences_secret",  # noqa: S106
            domain="example.com",
            email_preferences_service=email_preferences_service,
            use_secure_cookie=True,
        )


@pytest.mark.usefixtures("pyramid_config")
class TestLTIUserSecurityPolicy:
    def test_it_returns_empty_identity_if_theres_no_lti_user(
        self, pyramid_request, get_lti_user, policy
    ):
        get_lti_user.return_value = None

        assert not policy.identity(pyramid_request)

    def test_it_returns_empty_identity_if_validation_error(
        self, pyramid_request, policy, get_lti_user
    ):
        get_lti_user.side_effect = ValidationError(sentinel.messages)

        assert not policy.identity(pyramid_request)

    @pytest.mark.usefixtures("user_has_no_roles")
    def test_identity_when_theres_an_lti_user_with_no_roles(
        self, pyramid_request, policy, get_lti_user
    ):
        get_lti_user.return_value = pyramid_request.lti_user

        identity = policy.identity(pyramid_request)

        assert not identity.permissions
        assert identity.userid

    @pytest.mark.parametrize("is_instructor", [True, False])
    def test_identity_when_theres_an_lti_user(
        self,
        request,
        pyramid_request,
        is_instructor,
        policy,
        get_lti_user,
    ):
        if is_instructor:
            _ = request.getfixturevalue("user_is_instructor")
        else:
            _ = request.getfixturevalue("user_is_learner")
        get_lti_user.return_value = pyramid_request.lti_user

        identity = policy.identity(pyramid_request)

        assert identity.userid

        expected_permissions = [
            Permissions.LTI_LAUNCH_ASSIGNMENT,
            Permissions.API,
        ]

        if is_instructor:
            expected_permissions.extend(
                [
                    Permissions.LTI_CONFIGURE_ASSIGNMENT,
                    Permissions.GRADE_ASSIGNMENT,
                    Permissions.DASHBOARD_VIEW,
                ]
            )

        assert identity.permissions == expected_permissions

    def test_permits_allow(
        self, pyramid_request, user_is_learner, policy, get_lti_user
    ):
        get_lti_user.return_value = user_is_learner

        is_allowed = policy.permits(
            pyramid_request, None, Permissions.LTI_LAUNCH_ASSIGNMENT
        )

        assert is_allowed == Allowed("allowed")

    def test_permits_denied(self, pyramid_request, policy, get_lti_user):
        get_lti_user.return_value = None

        is_allowed = policy.permits(pyramid_request, None, "some-permission")

        assert is_allowed == Denied("denied")

    def test_permits_denied_with_validation_error(
        self, pyramid_request, policy, get_lti_user
    ):
        validation_error = ValidationError(sentinel.message)
        get_lti_user.side_effect = validation_error

        is_allowed = policy.permits(pyramid_request, None, "some-permission")

        assert is_allowed == DeniedWithException(validation_error)

    @pytest.mark.parametrize(
        "user_id,application_instance_id,expected_userid",
        [
            (None, None, None),
            ("sam", 100, "c2Ft:100"),
        ],
    )
    def test_authenticated_userid(
        self,
        user_id,
        application_instance_id,
        expected_userid,
        pyramid_request,
        get_lti_user,
        policy,
    ):
        get_lti_user.return_value = (
            factories.LTIUser(
                user_id=user_id, application_instance_id=application_instance_id
            )
            if user_id
            else None
        )

        assert policy.authenticated_userid(pyramid_request) == expected_userid

    @pytest.fixture
    def policy(self):
        return LTIUserSecurityPolicy()

    @pytest.fixture
    def get_lti_user(self, policy):
        with patch.object(policy, "get_lti_user") as get_lti_user:
            yield get_lti_user


class TestSecurityPolicy:
    def test_authenticated_userid(self, policy, get_policy, pyramid_request):
        user_id = policy.authenticated_userid(pyramid_request)

        get_policy.assert_called_once_with(pyramid_request)
        get_policy.return_value.authenticated_userid.assert_called_once_with(
            pyramid_request
        )
        assert user_id == get_policy.return_value.authenticated_userid.return_value

    def test_identity(self, policy, get_policy, pyramid_request):
        user_id = policy.identity(pyramid_request)

        get_policy.assert_called_once_with(pyramid_request)
        get_policy.return_value.identity.assert_called_once_with(pyramid_request)
        assert user_id == get_policy.return_value.identity.return_value

    def test_permits(self, policy, get_policy, pyramid_request):
        user_id = policy.permits(pyramid_request, sentinel.context, sentinel.permission)

        get_policy.assert_called_once_with(pyramid_request)
        get_policy.return_value.permits.assert_called_once_with(
            pyramid_request, sentinel.context, sentinel.permission
        )
        assert user_id == get_policy.return_value.permits.return_value

    def test_remember(self, policy, get_policy, pyramid_request):
        user_id = policy.remember(
            pyramid_request, sentinel.userid, kwarg=sentinel.kwargs
        )

        get_policy.assert_called_once_with(pyramid_request)
        get_policy.return_value.remember.assert_called_once_with(
            pyramid_request, sentinel.userid, kwarg=sentinel.kwargs
        )
        assert user_id == get_policy.return_value.remember.return_value

    def test_forgets(self, policy, pyramid_request, get_policy):
        user_id = policy.forget(pyramid_request)

        get_policy.assert_called_once_with(pyramid_request)
        get_policy.return_value.forget.assert_called_once_with(pyramid_request)
        assert user_id == get_policy.return_value.forget.return_value

    @pytest.mark.parametrize(
        "header_value,google_value,expected_policy",
        [
            (sentinel.ok, None, HeadersBearerTokenLTIUserPolicy),
            (None, sentinel.ok, LMSGoogleSecurityPolicy),
            (sentinel.ok, sentinel.ok, HeadersBearerTokenLTIUserPolicy),
            (None, None, HeadersBearerTokenLTIUserPolicy),
        ],
    )
    def test_api_dashboard_policy(
        self,
        pyramid_request,
        header_value,
        google_value,
        expected_policy,
        HeadersBearerTokenLTIUserPolicy,
        LMSGoogleSecurityPolicy,
    ):
        pyramid_request.path = "/api/dashboard/assignments/10"
        HeadersBearerTokenLTIUserPolicy.return_value.identity.return_value = (
            header_value
        )
        LMSGoogleSecurityPolicy.return_value.identity.return_value = google_value

        policy = SecurityPolicy.get_policy(pyramid_request)

        assert policy.__class__ == expected_policy

    @pytest.mark.parametrize(
        "path",
        ["/admin", "/admin/instance", "/googleauth"],
    )
    def test_get_policy_google(self, pyramid_request, path, LMSGoogleSecurityPolicy):
        pyramid_request.path = path
        policy = SecurityPolicy.get_policy(pyramid_request)

        assert policy == LMSGoogleSecurityPolicy.return_value

    @pytest.mark.parametrize(
        "path,expected_policy,",
        [
            ("/lti_launches", LaunchParamsLTIUserPolicy),
            ("/content_item_selection", LaunchParamsLTIUserPolicy),
            ("/canvas_oauth_callback", OAuthCallbackLTIUserPolicy),
            ("/api/blackboard/oauth/callback", OAuthCallbackLTIUserPolicy),
            ("/api/canvas_studio/oauth/callback", OAuthCallbackLTIUserPolicy),
            ("/api/d2l/oauth/callback", OAuthCallbackLTIUserPolicy),
            ("/api/canvas/oauth/authorize", QueryStringBearerTokenLTIUserPolicy),
            ("/api/canvas_studio/oauth/authorize", QueryStringBearerTokenLTIUserPolicy),
            ("/api/d2l/oauth/authorize", QueryStringBearerTokenLTIUserPolicy),
            ("/api/blackboard/oauth/authorize", QueryStringBearerTokenLTIUserPolicy),
            ("/api/moodle/pages/proxy", QueryStringBearerTokenLTIUserPolicy),
            ("/api/canvas/pages/proxy", QueryStringBearerTokenLTIUserPolicy),
            ("/api/canvas/files", HeadersBearerTokenLTIUserPolicy),
            ("/api/blackboard/groups", HeadersBearerTokenLTIUserPolicy),
            ("/api/dashboard/assignments/X", HeadersBearerTokenLTIUserPolicy),
            ("/api/dashboard/assignments/X/stats", HeadersBearerTokenLTIUserPolicy),
            ("/api/dashboard/courses/X", HeadersBearerTokenLTIUserPolicy),
            (
                "/api/dashboard/courses/X/assignments/stats",
                HeadersBearerTokenLTIUserPolicy,
            ),
            ("/lti/1.3/deep_linking/form_fields", HeadersBearerTokenLTIUserPolicy),
            ("/lti/1.1/deep_linking/form_fields", HeadersBearerTokenLTIUserPolicy),
            ("/lti/reconfigure", HeadersBearerTokenLTIUserPolicy),
            ("/assignment", FormBearerTokenLTIUserPolicy),
            ("/assignment/edit", FormBearerTokenLTIUserPolicy),
            ("/dashboard/launch/assignments/10", FormBearerTokenLTIUserPolicy),
            ("/dashboard/assignments/10", CookiesBearerTokenLTIUserPolicy),
            ("/dashboard/orgs/ORGID/assignments/10", LMSGoogleSecurityPolicy),
        ],
    )
    def test_get_policy_lti_user(
        self, pyramid_request, path, expected_policy, policy, LMSGoogleSecurityPolicy
    ):
        LMSGoogleSecurityPolicy.return_value.identity.return_value = None

        pyramid_request.path = path
        policy = policy.get_policy(pyramid_request)

        assert policy.__class__ == expected_policy

    @pytest.mark.parametrize("path", ["/email/preferences", "/email/unsubscribe"])
    def test_get_policy_email_preferences(
        self,
        pyramid_request,
        policy,
        email_preferences_service,
        EmailPreferencesSecurityPolicy,
        path,
    ):
        pyramid_request.path = path

        sub_policy = policy.get_policy(pyramid_request)

        EmailPreferencesSecurityPolicy.assert_called_once_with(
            secret="test_email_preferences_secret",  # noqa: S106
            domain="example.com",
            email_preferences_service=email_preferences_service,
            use_secure_cookie=True,
        )
        assert sub_policy == EmailPreferencesSecurityPolicy.return_value

    def test_unauthorized_policy(
        self, pyramid_request, UnautheticatedSecurityPolicy, policy
    ):
        pyramid_request.path = "/unknown"
        policy = policy.get_policy(pyramid_request)

        UnautheticatedSecurityPolicy.assert_called_once()
        assert policy == UnautheticatedSecurityPolicy.return_value

    @pytest.fixture(autouse=True)
    def LTIUserSecurityPolicy(self, patch):
        return patch("lms.security.LTIUserSecurityPolicy")

    @pytest.fixture(autouse=True)
    def LMSGoogleSecurityPolicy(self, patch):
        return patch("lms.security.LMSGoogleSecurityPolicy")

    @pytest.fixture(autouse=True)
    def HeadersBearerTokenLTIUserPolicy(self, patch):
        return patch("lms.security.HeadersBearerTokenLTIUserPolicy")

    @pytest.fixture(autouse=True)
    def EmailPreferencesSecurityPolicy(self, patch):
        return patch("lms.security.EmailPreferencesSecurityPolicy")

    @pytest.fixture(autouse=True)
    def UnautheticatedSecurityPolicy(self, patch):
        return patch("lms.security.UnautheticatedSecurityPolicy")

    @pytest.fixture
    def get_policy(self, policy):
        with patch.object(policy, "get_policy") as get_policy:
            yield get_policy

    @pytest.fixture
    def policy(self):
        return SecurityPolicy()


@pytest.mark.usefixtures("user_service")
class TestLaunchParamsLTIUserPolicy:
    def test_it_with_lti11(self, LTI11AuthSchema, lti11_auth_schema, pyramid_request):
        lti_user = LaunchParamsLTIUserPolicy().get_lti_user(pyramid_request)

        LTI11AuthSchema.assert_called_once_with(pyramid_request)
        assert lti_user == lti11_auth_schema.lti_user.return_value

    def test_it_with_lti13(self, LTI13AuthSchema, lti13_auth_schema, pyramid_request):
        pyramid_request.params = {"id_token": sentinel.token}
        lti_user = LaunchParamsLTIUserPolicy().get_lti_user(pyramid_request)

        LTI13AuthSchema.assert_called_once_with(pyramid_request)
        assert lti_user == lti13_auth_schema.lti_user.return_value

    @pytest.fixture(autouse=True)
    def LTI11AuthSchema(self, patch):
        return patch("lms.security.LTI11AuthSchema")

    @pytest.fixture
    def lti11_auth_schema(self, LTI11AuthSchema):
        return LTI11AuthSchema.return_value

    @pytest.fixture(autouse=True)
    def LTI13AuthSchema(self, patch):
        return patch("lms.security.LTI13AuthSchema")

    @pytest.fixture
    def lti13_auth_schema(self, LTI13AuthSchema):
        return LTI13AuthSchema.return_value


@pytest.mark.usefixtures("user_service")
class TestBearerTokenLTIUserPolicies:
    @pytest.mark.parametrize(
        "policy_class,location",
        [
            (FormBearerTokenLTIUserPolicy, "form"),
            (CookiesBearerTokenLTIUserPolicy, "cookies"),
            (HeadersBearerTokenLTIUserPolicy, "headers"),
            (QueryStringBearerTokenLTIUserPolicy, "querystring"),
        ],
    )
    def test_it(
        self,
        BearerTokenSchema,
        bearer_token_schema,
        pyramid_request,
        policy_class,
        location,
    ):
        lti_user = policy_class().get_lti_user(pyramid_request)

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.lti_user.assert_called_once_with(location=location)
        assert lti_user == bearer_token_schema.lti_user.return_value

    @pytest.fixture(autouse=True)
    def BearerTokenSchema(self, patch):
        return patch("lms.security.BearerTokenSchema")

    @pytest.fixture
    def bearer_token_schema(self, BearerTokenSchema):
        return BearerTokenSchema.return_value


@pytest.mark.usefixtures("user_service")
class TestOAuthCallbackLTIUserPolicy:
    def test_it(self, OAuthCallbackSchema, oauth_callback_schema, pyramid_request):
        lti_user = OAuthCallbackLTIUserPolicy().get_lti_user(pyramid_request)

        OAuthCallbackSchema.assert_called_once_with(pyramid_request)
        assert lti_user == oauth_callback_schema.lti_user.return_value

    @pytest.fixture(autouse=True)
    def OAuthCallbackSchema(self, patch):
        return patch("lms.security.OAuthCallbackSchema")

    @pytest.fixture
    def oauth_callback_schema(self, OAuthCallbackSchema):
        return OAuthCallbackSchema.return_value


@pytest.mark.usefixtures("user_service")
class TestGetLTIUser:
    @pytest.mark.usefixtures("pyramid_request_with_identity")
    def test_it(self, pyramid_request, user_service, lti_user, sentry_sdk):
        result = get_lti_user(pyramid_request)

        assert result == lti_user
        user_service.upsert_user.assert_called_once_with(result)
        sentry_sdk.set_tag.assert_called_once_with(
            "application_instance_id", lti_user.application_instance_id
        )

    def test_it_when_no_lti_user(self, pyramid_request):
        lti_user = get_lti_user(pyramid_request)

        assert not lti_user

    @pytest.fixture
    def pyramid_request_with_identity(self, pyramid_config, pyramid_request, lti_user):
        pyramid_config.testing_securitypolicy(
            userid=sentinel.userid,
            identity=Identity(sentinel.userid, sentinel.permissions, lti_user),
        )
        return pyramid_request

    @pytest.fixture
    def sentry_sdk(self, patch):
        return patch("lms.security.sentry_sdk")


class TestGetUser:
    def test_it(self, pyramid_request, user_service):
        user = _get_user(pyramid_request)

        user_service.get.assert_called_once_with(
            pyramid_request.lti_user.application_instance,
            pyramid_request.lti_user.user_id,
        )
        assert user == user_service.get.return_value

    def test_it_when_no_lti_user(self, pyramid_request):
        pyramid_request.lti_user = None

        assert not _get_user(pyramid_request)


@pytest.fixture(autouse=True)
def AuthTktCookieHelper(patch):
    return patch("lms.security.AuthTktCookieHelper")
