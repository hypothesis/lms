from unittest import mock
from unittest.mock import call, sentinel

import pytest
from pyramid.interfaces import ISecurityPolicy
from pyramid.security import Allowed, Denied

from lms.security import (
    Identity,
    LMSGoogleSecurityPolicy,
    LTIUserSecurityPolicy,
    Permissions,
    SecurityPolicy,
    _get_lti_user,
    _get_user,
    includeme,
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
class TestLTIUserSecurityPolicy:
    def test_it_returns_empty_identity_if_theres_no_lti_user(
        self, pyramid_request, _get_lti_user
    ):
        _get_lti_user.return_value = None
        policy = LTIUserSecurityPolicy()
        userid = policy.identity(pyramid_request)

        assert userid == Identity(userid="", permissions=[])

    @pytest.mark.parametrize(
        "roles,extra_permissions",
        (
            ("administrator,noise", [Permissions.LTI_CONFIGURE_ASSIGNMENT]),
            ("instructor,noise", [Permissions.LTI_CONFIGURE_ASSIGNMENT]),
            ("INSTRUCTOR,noise", [Permissions.LTI_CONFIGURE_ASSIGNMENT]),
            ("teachingassistant,noise", [Permissions.LTI_CONFIGURE_ASSIGNMENT]),
            ("other", []),
        ),
    )
    def test_identity_when_theres_an_lti_user(
        self, pyramid_request, roles, extra_permissions, _get_lti_user
    ):
        policy = LTIUserSecurityPolicy()
        _get_lti_user.return_value = pyramid_request.lti_user._replace(roles=roles)

        identity = policy.identity(pyramid_request)

        assert identity.userid
        assert (
            identity.permissions
            == [Permissions.LTI_LAUNCH_ASSIGNMENT, Permissions.API] + extra_permissions
        )

    def test_remember(self, pyramid_request):
        LTIUserSecurityPolicy().remember(
            pyramid_request, "TEST_USERID", kwarg=mock.sentinel.kwarg
        )

    def test_forget(self, pyramid_request):
        LTIUserSecurityPolicy().forget(pyramid_request)

    def test_permits_allow(self, pyramid_request, _get_lti_user):
        _get_lti_user.return_value = factories.LTIUser()
        policy = LTIUserSecurityPolicy()
        is_allowed = policy.permits(
            pyramid_request, None, Permissions.LTI_LAUNCH_ASSIGNMENT
        )

        assert is_allowed == Allowed("allowed")

    def test_permits_denied(self, pyramid_request, _get_lti_user):
        _get_lti_user.return_value = None

        policy = LTIUserSecurityPolicy()

        is_allowed = policy.permits(pyramid_request, None, "some-permission")

        assert is_allowed == Denied("denied")

    @pytest.mark.parametrize(
        "lti_user,expected_userid",
        [
            (None, None),
            (
                factories.LTIUser(
                    user_id="sam",
                    application_instance_id=100,
                ),
                "c2Ft:100",
            ),
        ],
    )
    def test_authenticated_userid(
        self, lti_user, expected_userid, pyramid_request, _get_lti_user
    ):
        policy = LTIUserSecurityPolicy()
        _get_lti_user.return_value = lti_user

        assert policy.authenticated_userid(pyramid_request) == expected_userid

    @pytest.fixture()
    def _get_lti_user(self, patch):
        return patch("lms.security._get_lti_user")


class TestSecurityPolicy:
    def test_it_returns_the_userid_from_LTIUserSecurityPolicy(
        self, policy, LTIUserSecurityPolicy, lti_security_policy, pyramid_request
    ):
        lti_security_policy.authenticated_userid.return_value = "user"
        user_id = policy.authenticated_userid(pyramid_request)

        LTIUserSecurityPolicy.assert_called_once_with()
        lti_security_policy.authenticated_userid.assert_called_with(pyramid_request)
        assert user_id == "user"

    def test_it_falls_back_on_LMSGoogleSecurityPolicy(
        self, lti_security_policy, google_security_policy, policy, pyramid_request
    ):
        lti_security_policy.authenticated_userid.return_value = None

        google_security_policy.authenticated_userid.return_value = "google-oauth-user"

        user_id = policy.authenticated_userid(pyramid_request)

        google_security_policy.authenticated_userid.assert_called_with(pyramid_request)
        assert user_id == "google-oauth-user"

    def test_it_falls_back_to_last(
        self, lti_security_policy, google_security_policy, policy, pyramid_request
    ):
        lti_security_policy.authenticated_userid.return_value = None
        google_security_policy.authenticated_userid.return_value = None

        user_id = policy.authenticated_userid(pyramid_request)

        google_security_policy.authenticated_userid.assert_called_with(pyramid_request)
        assert user_id is None

    def test_remember_delegates_to_LTIUserSecurityPolicy(
        self, policy, LTIUserSecurityPolicy, lti_security_policy, pyramid_request
    ):
        policy.remember(
            pyramid_request, mock.sentinel.userid, kwarg=mock.sentinel.kwarg
        )

        LTIUserSecurityPolicy.assert_called_once_with()
        lti_security_policy.remember.assert_called_once_with(
            pyramid_request, mock.sentinel.userid, kwarg=mock.sentinel.kwarg
        )

    def test_forget_delegates_to_LTIUserSecurityPolicy(
        self, policy, LTIUserSecurityPolicy, lti_security_policy, pyramid_request
    ):
        policy.forget(pyramid_request)

        LTIUserSecurityPolicy.assert_called_once_with()
        lti_security_policy.forget.assert_called_once_with(pyramid_request)

    def test_identity_delegates_to_LTIUserSecurityPolicy(
        self, policy, LTIUserSecurityPolicy, lti_security_policy, pyramid_request
    ):
        policy.identity(pyramid_request)

        LTIUserSecurityPolicy.assert_called_once_with()
        lti_security_policy.identity.assert_called_once_with(pyramid_request)

    def test_permits_delegates_to_LTIUserSecurityPolicy(
        self, policy, LTIUserSecurityPolicy, lti_security_policy, pyramid_request
    ):
        policy.permits(pyramid_request, mock.sentinel.context, "some-permission")

        LTIUserSecurityPolicy.assert_called_once_with()
        lti_security_policy.permits.assert_called_once_with(
            pyramid_request, mock.sentinel.context, "some-permission"
        )

    @pytest.fixture
    def policy(self):
        return SecurityPolicy()

    @pytest.fixture(autouse=True)
    def LTIUserSecurityPolicy(self, patch):
        return patch("lms.security.LTIUserSecurityPolicy")

    @pytest.fixture(autouse=True)
    def LMSGoogleSecurityPolicy(self, patch):
        return patch("lms.security.LMSGoogleSecurityPolicy")

    @pytest.fixture
    def lti_security_policy(self, LTIUserSecurityPolicy):
        return LTIUserSecurityPolicy.return_value

    @pytest.fixture
    def google_security_policy(self, LMSGoogleSecurityPolicy):
        return LMSGoogleSecurityPolicy.return_value


@pytest.mark.usefixtures("user_service")
class TestGetLTIUser:
    def test_it_returns_the_LTIUsers_from_LTI_launch_params(
        self, bearer_token_schema, LTI11AuthSchema, lti11_auth_schema, pyramid_request
    ):
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        lti_user = _get_lti_user(pyramid_request)

        LTI11AuthSchema.assert_called_once_with(pyramid_request)
        lti11_auth_schema.lti_user.assert_called_once_with()
        assert lti_user == lti11_auth_schema.lti_user.return_value

    def test_it_returns_LTIUsers_from_authorization_headers(
        self, lti11_auth_schema, BearerTokenSchema, bearer_token_schema, pyramid_request
    ):
        lti11_auth_schema.lti_user.side_effect = ValidationError(["TEST_ERROR_MESSAGE"])

        lti_user = _get_lti_user(pyramid_request)

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.lti_user.assert_called_once_with(location="headers")
        assert lti_user == bearer_token_schema.lti_user.return_value

    def test_it_returns_LTIUsers_from_authorization_query_string_params(
        self, lti11_auth_schema, bearer_token_schema, pyramid_request
    ):
        lti11_auth_schema.lti_user.side_effect = ValidationError(["TEST_ERROR_MESSAGE"])
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
        self, lti11_auth_schema, bearer_token_schema, pyramid_request
    ):
        lti11_auth_schema.lti_user.side_effect = ValidationError(["TEST_ERROR_MESSAGE"])
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
        lti11_auth_schema,
        bearer_token_schema,
        OAuthCallbackSchema,
        canvas_oauth_callback_schema,
        pyramid_request,
    ):
        lti11_auth_schema.lti_user.side_effect = ValidationError(["TEST_ERROR_MESSAGE"])
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        lti_user = _get_lti_user(pyramid_request)

        OAuthCallbackSchema.assert_called_once_with(pyramid_request)
        canvas_oauth_callback_schema.lti_user.assert_called_once_with()
        assert lti_user == canvas_oauth_callback_schema.lti_user.return_value

    def test_it_returns_LTIUser_from_openid_auth_schema(
        self, LTI13AuthSchema, lti13_auth_schema, pyramid_request
    ):
        pyramid_request.params["id_token"] = "JWT"

        lti_user = _get_lti_user(pyramid_request)

        LTI13AuthSchema.assert_called_once_with(pyramid_request)
        lti13_auth_schema.lti_user.assert_called_once()
        assert lti_user == lti13_auth_schema.lti_user.return_value

    def test_it_returns_None_if_all_schemas_fail(
        self,
        lti11_auth_schema,
        bearer_token_schema,
        canvas_oauth_callback_schema,
        pyramid_request,
    ):
        lti11_auth_schema.lti_user.side_effect = ValidationError(["TEST_ERROR_MESSAGE"])
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        canvas_oauth_callback_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        assert _get_lti_user(pyramid_request) is None

    def test_LTI11AuthSchema_overrides_BearerTokenSchema(
        self, lti11_auth_schema, pyramid_request
    ):
        assert _get_lti_user(pyramid_request) == lti11_auth_schema.lti_user.return_value

    def test_it_stores_the_user(self, pyramid_request, user_service, lti11_auth_schema):
        _get_lti_user(pyramid_request)

        user_service.upsert_user.assert_called_once_with(
            lti11_auth_schema.lti_user.return_value
        )

    @pytest.fixture(autouse=True)
    def BearerTokenSchema(self, patch):
        return patch("lms.security.BearerTokenSchema")

    @pytest.fixture
    def bearer_token_schema(self, BearerTokenSchema):
        return BearerTokenSchema.return_value

    @pytest.fixture(autouse=True)
    def OAuthCallbackSchema(self, patch):
        return patch("lms.security.OAuthCallbackSchema")

    @pytest.fixture(autouse=True)
    def LTI13AuthSchema(self, patch):
        return patch("lms.security.LTI13AuthSchema")

    @pytest.fixture
    def lti13_auth_schema(self, LTI13AuthSchema):
        return LTI13AuthSchema.return_value

    @pytest.fixture
    def canvas_oauth_callback_schema(self, OAuthCallbackSchema):
        return OAuthCallbackSchema.return_value

    @pytest.fixture(autouse=True)
    def LTI11AuthSchema(self, patch):
        return patch("lms.security.LTI11AuthSchema")

    @pytest.fixture
    def lti11_auth_schema(self, LTI11AuthSchema):
        return LTI11AuthSchema.return_value


class TestGetUser:
    def test_it(self, pyramid_request, user_service, application_instance_service):
        user = _get_user(pyramid_request)

        user_service.get.assert_called_once_with(
            application_instance_service.get_current.return_value,
            pyramid_request.lti_user.user_id,
        )
        assert user == user_service.get.return_value
