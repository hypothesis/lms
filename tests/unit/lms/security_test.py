from unittest import mock
from unittest.mock import call, sentinel

import pytest
from pyramid.interfaces import ISecurityPolicy
from pyramid.security import Allowed, Denied

from lms.security import (
    AuthTktCookieSecurityPolicy,
    Identity,
    LMSGoogleSecurityPolicy,
    LTISecurityPolicy,
    Permissions,
    SecurityPolicy,
    _authenticated_userid,
    _get_lti_user,
    includeme,
)
from lms.validation import ValidationError
from tests import factories


class TestIncludeMe:
    def test_it_sets_security_policy(self, pyramid_config, SecurityPolicy):
        includeme(pyramid_config)

        SecurityPolicy.assert_called_once_with("TEST_LMS_SECRET")
        assert (
            pyramid_config.registry.queryUtility(ISecurityPolicy)
            == SecurityPolicy.return_value
        )

    @pytest.fixture(autouse=True)
    def SecurityPolicy(self, patch):
        return patch("lms.security.SecurityPolicy")


@pytest.mark.usefixtures("pyramid_config")
class TestAuthTktCookieSecurityPolicy:
    def test_it_returns_empty_identity_no_cookie(self, pyramid_request):
        policy = AuthTktCookieSecurityPolicy("TEST_LMS_SECRET")

        identity = policy.identity(pyramid_request)

        assert not identity.userid
        assert identity.permissions == []

    def test_it_returns_identity_from_cookie(
        self, pyramid_request, AuthTktCookieHelper
    ):
        AuthTktCookieHelper.return_value.identify.return_value = {"userid": "testuser"}

        policy = AuthTktCookieSecurityPolicy("TEST_LMS_SECRET")

        identity = policy.identity(pyramid_request)

        assert identity.userid == "testuser"
        assert identity.permissions == []

    def test_it_returns_identity_from_cookie_for_reports(
        self, pyramid_request, AuthTktCookieHelper
    ):
        AuthTktCookieHelper.return_value.identify.return_value = {
            "userid": "report_viewer"
        }

        policy = AuthTktCookieSecurityPolicy("TEST_LMS_SECRET")

        identity = policy.identity(pyramid_request)

        assert identity.userid == "report_viewer"
        assert identity.permissions == [Permissions.REPORTS_VIEW]

    def test_it_returns_userid_matches_identity(
        self, pyramid_request, AuthTktCookieHelper
    ):
        AuthTktCookieHelper.return_value.identify.return_value = {"userid": "testuser"}

        policy = AuthTktCookieSecurityPolicy("TEST_LMS_SECRET")

        userid = policy.authenticated_userid(pyramid_request)

        assert userid == "testuser"

    def test_permits_allow(self, pyramid_request, AuthTktCookieHelper):
        AuthTktCookieHelper.return_value.identify.return_value = {
            "userid": "report_viewer"
        }

        policy = AuthTktCookieSecurityPolicy("TEST_LMS_SECRET")

        is_allowed = policy.permits(pyramid_request, None, Permissions.REPORTS_VIEW)

        assert is_allowed == Allowed("allowed")

    def test_permits_denied(self, pyramid_request, AuthTktCookieHelper):
        AuthTktCookieHelper.return_value.identify.return_value = {"userid": "testuser"}

        policy = AuthTktCookieSecurityPolicy("TEST_LMS_SECRET")

        is_allowed = policy.permits(pyramid_request, None, "some-permission")

        assert is_allowed == Denied("denied")

    def test_remember(self, pyramid_request, AuthTktCookieHelper):
        AuthTktCookieSecurityPolicy("TEST_LMS_SECRET").remember(
            pyramid_request, "TEST_USERID"
        )

        AuthTktCookieHelper.return_value.remember.assert_called_once()

    def test_forget(self, pyramid_request, AuthTktCookieHelper):
        AuthTktCookieSecurityPolicy("TEST_LMS_SECRET").forget(pyramid_request)

        AuthTktCookieHelper.return_value.forget.assert_called_once()

    @pytest.fixture
    def AuthTktCookieHelper(self, patch):
        return patch("lms.security.AuthTktCookieHelper")


class TestLMSGoogleSecurityPolicy:
    @pytest.mark.parametrize(
        "userid,expected_identity",
        [
            (
                "testuser@hypothes.is",
                Identity(
                    userid="testuser@hypothes.is",
                    permissions=[Permissions.ADMIN],
                ),
            ),
            ("testuser@example.com", Identity(userid="", permissions=[])),
        ],
    )
    def test_identity(self, policy, pyramid_request, userid, expected_identity):
        pyramid_request.session["googleauth.userid"] = userid

        assert policy.identity(pyramid_request) == expected_identity

    def test_identity_when_no_user_is_logged_in(self, policy, pyramid_request):
        assert policy.identity(pyramid_request) == Identity(userid="", permissions=[])

    def test_authenticated_userid(self, policy, pyramid_request):
        pyramid_request.session["googleauth.userid"] = "testuser@hypothes.is"

        assert policy.authenticated_userid(pyramid_request) == "testuser@hypothes.is"

    @pytest.mark.parametrize(
        "permission,expected_result",
        [
            (Permissions.ADMIN, Allowed("allowed")),
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


@pytest.mark.usefixtures("pyramid_config")
class TestLTISecurityPolicy:
    def test_it_returns_the_lti_userid(self, pyramid_request, _authenticated_userid):
        policy = LTISecurityPolicy()

        userid = policy.authenticated_userid(pyramid_request)

        _authenticated_userid.assert_called_once_with(pyramid_request.lti_user)
        assert userid == _authenticated_userid.return_value

    def test_it_returns_empty_identity_if_theres_no_lti_user(self, pyramid_request):
        pyramid_request.lti_user = None
        policy = LTISecurityPolicy()
        userid = policy.identity(pyramid_request)

        assert userid == Identity(userid="", permissions=[])

    def test_identity_when_theres_an_lti_user(
        self, pyramid_request, _authenticated_userid
    ):
        policy = LTISecurityPolicy()

        identity = policy.identity(pyramid_request)

        _authenticated_userid.assert_called_once_with(pyramid_request.lti_user)
        assert identity == Identity(
            userid=_authenticated_userid.return_value,
            permissions=[Permissions.LTI_LAUNCH_ASSIGNMENT, Permissions.API],
        )

    def test_remember(self, pyramid_request):
        LTISecurityPolicy().remember(
            pyramid_request, "TEST_USERID", kwarg=mock.sentinel.kwarg
        )

    def test_forget(self, pyramid_request):
        LTISecurityPolicy().forget(pyramid_request)

    def test_permits_allow(
        self,
        pyramid_request,
    ):
        pyramid_request.lti_user = "some-user"
        policy = LTISecurityPolicy()

        is_allowed = policy.permits(
            pyramid_request, None, Permissions.LTI_LAUNCH_ASSIGNMENT
        )

        assert is_allowed == Allowed("allowed")

    def test_permits_denied(self, pyramid_request):
        pyramid_request.lti_user = None

        policy = LTISecurityPolicy()

        is_allowed = policy.permits(pyramid_request, None, "some-permission")

        assert is_allowed == Denied("denied")

    @pytest.fixture(autouse=True)
    def _authenticated_userid(self, patch):
        return patch("lms.security._authenticated_userid")


class TestSecurityPolicy:
    def test_it_returns_the_userid_from_LTISecurityPolicy(
        self, policy, LTISecurityPolicy, lti_security_policy
    ):
        lti_security_policy.authenticated_userid.return_value = "user"
        user_id = policy.authenticated_userid(mock.sentinel.request)

        LTISecurityPolicy.assert_called_once_with()
        lti_security_policy.authenticated_userid.assert_called_with(
            mock.sentinel.request
        )
        assert user_id == "user"

    def test_it_falls_back_on_AuthTktCookieSecurityPolicy(
        self,
        tkt_security_policy,
        lti_security_policy,
        policy,
    ):
        lti_security_policy.authenticated_userid.return_value = None
        tkt_security_policy.authenticated_userid.return_value = "tkt-user"

        user_id = policy.authenticated_userid(mock.sentinel.request)

        tkt_security_policy.authenticated_userid.assert_called_with(
            mock.sentinel.request
        )
        assert user_id == "tkt-user"

    def test_it_falls_back_on_LMSGoogleSecurityPolicy(
        self,
        tkt_security_policy,
        lti_security_policy,
        google_security_policy,
        policy,
    ):
        lti_security_policy.authenticated_userid.return_value = None
        tkt_security_policy.authenticated_userid.return_value = None
        google_security_policy.authenticated_userid.return_value = "google-oauth-user"

        user_id = policy.authenticated_userid(mock.sentinel.request)

        google_security_policy.authenticated_userid.assert_called_with(
            mock.sentinel.request
        )
        assert user_id == "google-oauth-user"

    def test_it_falls_back_to_last(
        self,
        tkt_security_policy,
        lti_security_policy,
        google_security_policy,
        policy,
    ):
        lti_security_policy.authenticated_userid.return_value = None
        tkt_security_policy.authenticated_userid.return_value = None
        google_security_policy.authenticated_userid.return_value = None

        user_id = policy.authenticated_userid(mock.sentinel.request)

        google_security_policy.authenticated_userid.assert_called_with(
            mock.sentinel.request
        )
        assert user_id is None

    def test_remember_delegates_to_LTISecurityPolicy(
        self,
        policy,
        LTISecurityPolicy,
        lti_security_policy,
        tkt_security_policy,
    ):
        policy.remember(
            mock.sentinel.request, mock.sentinel.userid, kwarg=mock.sentinel.kwarg
        )

        LTISecurityPolicy.assert_called_once_with()
        lti_security_policy.remember.assert_called_once_with(
            mock.sentinel.request, mock.sentinel.userid, kwarg=mock.sentinel.kwarg
        )
        tkt_security_policy.remember.assert_not_called()

    def test_remember_falls_back_on_AuthTktCookieSecurityPolicy(
        self, policy, lti_security_policy, tkt_security_policy
    ):
        lti_security_policy.authenticated_userid.return_value = None

        policy.remember(
            mock.sentinel.request, mock.sentinel.userid, kwarg=mock.sentinel.kwarg
        )
        tkt_security_policy.remember.assert_called_once_with(
            mock.sentinel.request, mock.sentinel.userid, kwarg=mock.sentinel.kwarg
        )
        lti_security_policy.remember.assert_not_called()

    def test_forget_delegates_to_LTISecurityPolicy(
        self,
        policy,
        LTISecurityPolicy,
        lti_security_policy,
        tkt_security_policy,
    ):
        policy.forget(mock.sentinel.request)

        LTISecurityPolicy.assert_called_once_with()
        lti_security_policy.forget.assert_called_once_with(mock.sentinel.request)
        tkt_security_policy.forget.assert_not_called()

    def test_forget_falls_back_on_AuthTktCookieSecurityPolicy(
        self, policy, lti_security_policy, tkt_security_policy
    ):
        lti_security_policy.authenticated_userid.return_value = None

        policy.forget(mock.sentinel.request)
        tkt_security_policy.forget.assert_called_once_with(mock.sentinel.request)
        lti_security_policy.forget.assert_not_called()

    def test_identity_delegates_to_LTISecurityPolicy(
        self,
        policy,
        LTISecurityPolicy,
        lti_security_policy,
        tkt_security_policy,
    ):
        policy.identity(mock.sentinel.request)

        LTISecurityPolicy.assert_called_once_with()
        lti_security_policy.identity.assert_called_once_with(mock.sentinel.request)
        tkt_security_policy.identity.assert_not_called()

    def test_permits_delegates_to_LTISecurityPolicy(
        self,
        policy,
        LTISecurityPolicy,
        lti_security_policy,
        tkt_security_policy,
    ):
        policy.permits(mock.sentinel.request, mock.sentinel.context, "some-permission")

        LTISecurityPolicy.assert_called_once_with()
        lti_security_policy.permits.assert_called_once_with(
            mock.sentinel.request, mock.sentinel.context, "some-permission"
        )
        tkt_security_policy.permits.assert_not_called()

    @pytest.fixture
    def policy(self):
        return SecurityPolicy("TEST_SECRET")

    @pytest.fixture(autouse=True)
    def AuthTktCookieSecurityPolicy(self, patch):
        return patch("lms.security.AuthTktCookieSecurityPolicy")

    @pytest.fixture
    def tkt_security_policy(self, AuthTktCookieSecurityPolicy):
        return AuthTktCookieSecurityPolicy.return_value

    @pytest.fixture(autouse=True)
    def LTISecurityPolicy(self, patch):
        return patch("lms.security.LTISecurityPolicy")

    @pytest.fixture(autouse=True)
    def LMSGoogleSecurityPolicy(self, patch):
        return patch("lms.security.LMSGoogleSecurityPolicy")

    @pytest.fixture
    def lti_security_policy(self, LTISecurityPolicy):
        return LTISecurityPolicy.return_value

    @pytest.fixture
    def google_security_policy(self, LMSGoogleSecurityPolicy):
        return LMSGoogleSecurityPolicy.return_value


class TestAuthenticatedUserID:
    @pytest.mark.parametrize(
        "lti_user,expected_userid",
        [
            (
                factories.LTIUser(
                    user_id="sam",
                    oauth_consumer_key="Hypothesisf301584250a2dece14f021ab8424018a",
                ),
                "c2Ft:Hypothesisf301584250a2dece14f021ab8424018a",
            ),
            (
                factories.LTIUser(
                    user_id="Sam:Smith",
                    oauth_consumer_key="Hypothesisf301584250a2dece14f021ab8424018a",
                ),
                "U2FtOlNtaXRo:Hypothesisf301584250a2dece14f021ab8424018a",
            ),
        ],
    )
    def test_it(self, lti_user, expected_userid):
        assert _authenticated_userid(lti_user) == expected_userid


class TestGetLTIUser:
    def test_it_returns_the_LTIUsers_from_LTI_launch_params(
        self,
        bearer_token_schema,
        LaunchParamsAuthSchema,
        launch_params_auth_schema,
        pyramid_request,
    ):
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        lti_user = _get_lti_user(pyramid_request)

        LaunchParamsAuthSchema.assert_called_once_with(pyramid_request)
        launch_params_auth_schema.lti_user.assert_called_once_with()
        assert lti_user == launch_params_auth_schema.lti_user.return_value

    def test_it_returns_LTIUsers_from_authorization_headers(
        self,
        launch_params_auth_schema,
        BearerTokenSchema,
        bearer_token_schema,
        pyramid_request,
    ):
        launch_params_auth_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        lti_user = _get_lti_user(pyramid_request)

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.lti_user.assert_called_once_with(location="headers")
        assert lti_user == bearer_token_schema.lti_user.return_value

    def test_it_returns_LTIUsers_from_authorization_query_string_params(
        self, launch_params_auth_schema, bearer_token_schema, pyramid_request
    ):
        launch_params_auth_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        lti_user = factories.LTIUser()
        bearer_token_schema.lti_user.side_effect = [
            ValidationError(["TEST_ERROR_MESSAGE"]),
            lti_user,
            ValidationError(["TEST_ERROR_MESSAGE"]),
        ]

        returned_lti_user = _get_lti_user(pyramid_request)

        assert bearer_token_schema.lti_user.call_args_list == [
            call(location="headers"),
            call(location="querystring"),
        ]
        assert returned_lti_user == lti_user

    def test_it_returns_LTIUsers_from_authorization_form_fields(
        self, launch_params_auth_schema, bearer_token_schema, pyramid_request
    ):
        launch_params_auth_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        lti_user = factories.LTIUser()
        bearer_token_schema.lti_user.side_effect = [
            ValidationError(["TEST_ERROR_MESSAGE"]),
            ValidationError(["TEST_ERROR_MESSAGE"]),
            lti_user,
        ]

        returned_lti_user = _get_lti_user(pyramid_request)

        assert bearer_token_schema.lti_user.call_args_list == [
            call(location="headers"),
            call(location="querystring"),
            call(location="form"),
        ]
        assert returned_lti_user == lti_user

    def test_it_returns_LTIUsers_from_OAuth2_state_params(
        self,
        launch_params_auth_schema,
        bearer_token_schema,
        CanvasOAuthCallbackSchema,
        canvas_oauth_callback_schema,
        pyramid_request,
    ):
        launch_params_auth_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        lti_user = _get_lti_user(pyramid_request)

        CanvasOAuthCallbackSchema.assert_called_once_with(pyramid_request)
        canvas_oauth_callback_schema.lti_user.assert_called_once_with()
        assert lti_user == canvas_oauth_callback_schema.lti_user.return_value

    def test_it_returns_None_if_all_schemas_fail(
        self,
        launch_params_auth_schema,
        bearer_token_schema,
        canvas_oauth_callback_schema,
        pyramid_request,
    ):
        launch_params_auth_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        canvas_oauth_callback_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        assert _get_lti_user(pyramid_request) is None

    def test_LaunchParamsAuthSchema_overrides_BearerTokenSchema(
        self, launch_params_auth_schema, pyramid_request
    ):
        assert (
            _get_lti_user(pyramid_request)
            == launch_params_auth_schema.lti_user.return_value
        )

    @pytest.fixture(autouse=True)
    def BearerTokenSchema(self, patch):
        return patch("lms.security.BearerTokenSchema")

    @pytest.fixture
    def bearer_token_schema(self, BearerTokenSchema):
        return BearerTokenSchema.return_value

    @pytest.fixture(autouse=True)
    def CanvasOAuthCallbackSchema(self, patch):
        return patch("lms.security.CanvasOAuthCallbackSchema")

    @pytest.fixture
    def canvas_oauth_callback_schema(self, CanvasOAuthCallbackSchema):
        return CanvasOAuthCallbackSchema.return_value

    @pytest.fixture(autouse=True)
    def LaunchParamsAuthSchema(self, patch):
        return patch("lms.security.LaunchParamsAuthSchema")

    @pytest.fixture
    def launch_params_auth_schema(self, LaunchParamsAuthSchema):
        return LaunchParamsAuthSchema.return_value
