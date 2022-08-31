from unittest.mock import call, create_autospec, sentinel

import pytest
from pyramid.interfaces import ISecurityPolicy
from pyramid.security import Allowed, Denied

from lms.security import (
    DeniedWithValidationError,
    Identity,
    LMSGoogleSecurityPolicy,
    LTIUserSecurityPolicy,
    Permissions,
    SecurityPolicy,
    _get_user,
    get_lti_user,
    get_lti_user_from_launch_params,
    get_policy,
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
    def test_it_returns_empty_identity_if_theres_no_lti_user(self, pyramid_request):
        policy = LTIUserSecurityPolicy(create_autospec(get_lti_user, return_value=None))
        userid = policy.identity(pyramid_request)

        assert userid == Identity(userid="", permissions=[])

    def test_it_returns_empty_identity_if_validation_error(self, pyramid_request):
        get_lti_user_ = create_autospec(
            get_lti_user, side_effect=ValidationError(sentinel.messages)
        )

        policy = LTIUserSecurityPolicy(get_lti_user_)

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
        self, pyramid_request, roles, extra_permissions
    ):
        policy = LTIUserSecurityPolicy(
            create_autospec(
                get_lti_user,
                return_value=pyramid_request.lti_user._replace(roles=roles),
            )
        )

        identity = policy.identity(pyramid_request)

        assert identity.userid
        assert (
            identity.permissions
            == [Permissions.LTI_LAUNCH_ASSIGNMENT, Permissions.API] + extra_permissions
        )

    def test_remember(self, pyramid_request):
        LTIUserSecurityPolicy(sentinel.get_lti_user).remember(
            pyramid_request, "TEST_USERID", kwarg=sentinel.kwarg
        )

    def test_forget(self, pyramid_request):
        LTIUserSecurityPolicy(sentinel.get_lti_user).forget(pyramid_request)

    def test_permits_allow(self, pyramid_request):
        policy = LTIUserSecurityPolicy(
            create_autospec(get_lti_user, return_value=factories.LTIUser())
        )

        is_allowed = policy.permits(
            pyramid_request, None, Permissions.LTI_LAUNCH_ASSIGNMENT
        )

        assert is_allowed == Allowed("allowed")

    def test_permits_denied(self, pyramid_request):
        policy = LTIUserSecurityPolicy(create_autospec(get_lti_user, return_value=None))

        is_allowed = policy.permits(pyramid_request, None, "some-permission")

        assert is_allowed == Denied("denied")

    def test_permits_denied_with_validation_error(self, pyramid_request):
        validation_error = ValidationError(sentinel.message)
        policy = LTIUserSecurityPolicy(
            create_autospec(get_lti_user, side_effect=validation_error)
        )

        is_allowed = policy.permits(pyramid_request, None, "some-permission")

        assert is_allowed == DeniedWithValidationError(validation_error)

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
    def test_authenticated_userid(self, lti_user, expected_userid, pyramid_request):
        policy = LTIUserSecurityPolicy(
            create_autospec(get_lti_user, return_value=lti_user)
        )

        assert policy.authenticated_userid(pyramid_request) == expected_userid


class TestGetPolicy:
    @pytest.mark.parametrize(
        "route",
        ["/admin", "/admin/instance", "/googleauth"],
    )
    def test_picks_google_security_policy(
        self, route, pyramid_request, LMSGoogleSecurityPolicy
    ):
        pyramid_request.path = route

        policy = get_policy(pyramid_request)

        assert policy == LMSGoogleSecurityPolicy.return_value

    @pytest.mark.parametrize(
        "path",
        ["/lti_launches", "/content_item_selection", "/api/gateway/h/lti"],
    )
    def test_picks_lti_launches_security_policy(
        self, path, pyramid_request, LTIUserSecurityPolicy
    ):
        pyramid_request.path = path

        policy = get_policy(pyramid_request)

        LTIUserSecurityPolicy.assert_called_once_with(get_lti_user_from_launch_params)
        assert policy == LTIUserSecurityPolicy.return_value

    @pytest.mark.parametrize("path", ["/", "/api/canvas"])
    def test_picks_default_lti_user_security_policy(
        self, path, pyramid_request, LTIUserSecurityPolicy
    ):
        pyramid_request.path = path

        policy = get_policy(pyramid_request)

        LTIUserSecurityPolicy.assert_called_once_with(get_lti_user)
        assert policy == LTIUserSecurityPolicy.return_value

    @pytest.fixture(autouse=True)
    def LMSGoogleSecurityPolicy(self, patch):
        return patch("lms.security.LMSGoogleSecurityPolicy")

    @pytest.fixture(autouse=True)
    def LTIUserSecurityPolicy(self, patch):
        return patch("lms.security.LTIUserSecurityPolicy")


class TestSecurityPolicy:
    def test_authenticated_userid(self, policy, get_policy):
        user_id = policy.authenticated_userid(sentinel.request)

        get_policy.assert_called_once_with(sentinel.request)
        get_policy.return_value.authenticated_userid.assert_called_once_with(
            sentinel.request
        )
        assert user_id == get_policy.return_value.authenticated_userid.return_value

    def test_identity(self, policy, get_policy):
        user_id = policy.identity(sentinel.request)

        get_policy.assert_called_once_with(sentinel.request)
        get_policy.return_value.identity.assert_called_once_with(sentinel.request)
        assert user_id == get_policy.return_value.identity.return_value

    def test_permits(self, policy, get_policy):
        user_id = policy.permits(
            sentinel.request, sentinel.context, sentinel.permission
        )

        get_policy.assert_called_once_with(sentinel.request)
        get_policy.return_value.permits.assert_called_once_with(
            sentinel.request, sentinel.context, sentinel.permission
        )
        assert user_id == get_policy.return_value.permits.return_value

    def test_remember(self, policy, get_policy):
        user_id = policy.remember(
            sentinel.request, sentinel.userid, kwarg=sentinel.kwargs
        )

        get_policy.assert_called_once_with(sentinel.request)
        get_policy.return_value.remember.assert_called_once_with(
            sentinel.request, sentinel.userid, kwarg=sentinel.kwargs
        )
        assert user_id == get_policy.return_value.remember.return_value

    def test_forgets(self, policy, pyramid_request, get_policy):
        user_id = policy.forget(pyramid_request)

        get_policy.assert_called_once_with(pyramid_request)
        get_policy.return_value.forget.assert_called_once_with(pyramid_request)
        assert user_id == get_policy.return_value.forget.return_value

    @pytest.fixture
    def get_policy(self, patch):
        return patch("lms.security.get_policy")

    @pytest.fixture
    def policy(self):
        return SecurityPolicy()


@pytest.mark.usefixtures("user_service")
class TestGetLaunchesLTIUser:
    def test_it_with_lti11(self, LTI11AuthSchema, lti11_auth_schema, pyramid_request):
        lti_user = get_lti_user_from_launch_params(pyramid_request)

        LTI11AuthSchema.assert_called_once_with(pyramid_request)
        assert lti_user == lti11_auth_schema.lti_user.return_value

    def test_it_with_lti13(self, LTI13AuthSchema, lti13_auth_schema, pyramid_request):
        pyramid_request.params = {"id_token": sentinel.token}
        lti_user = get_lti_user_from_launch_params(pyramid_request)

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
class TestGetLTIUser:
    def test_it_returns_LTIUsers_from_authorization_headers(
        self, BearerTokenSchema, bearer_token_schema, pyramid_request
    ):
        lti_user = get_lti_user(pyramid_request)

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.lti_user.assert_called_once_with(location="headers")
        assert lti_user == bearer_token_schema.lti_user.return_value

    def test_it_returns_LTIUsers_from_authorization_query_string_params(
        self, bearer_token_schema, pyramid_request
    ):
        lti_user = factories.LTIUser()
        bearer_token_schema.lti_user.side_effect = [
            ValidationError(["TEST_ERROR_MESSAGE"]),
            lti_user,
            ValidationError(["TEST_ERROR_MESSAGE"]),
        ]

        returned_lti_user = get_lti_user(pyramid_request)

        assert bearer_token_schema.lti_user.call_args_list == [
            call(location="headers"),
            call(location="querystring"),
        ]
        assert returned_lti_user == lti_user

    def test_it_returns_LTIUsers_from_authorization_form_fields(
        self, bearer_token_schema, pyramid_request
    ):
        lti_user = factories.LTIUser()
        bearer_token_schema.lti_user.side_effect = [
            ValidationError(["TEST_ERROR_MESSAGE"]),
            ValidationError(["TEST_ERROR_MESSAGE"]),
            lti_user,
        ]

        returned_lti_user = get_lti_user(pyramid_request)

        assert bearer_token_schema.lti_user.call_args_list == [
            call(location="headers"),
            call(location="querystring"),
            call(location="form"),
        ]
        assert returned_lti_user == lti_user

    def test_it_returns_LTIUsers_from_OAuth2_state_params(
        self,
        bearer_token_schema,
        OAuthCallbackSchema,
        oauth_callback_schema,
        pyramid_request,
    ):
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        lti_user = get_lti_user(pyramid_request)

        OAuthCallbackSchema.assert_called_once_with(pyramid_request)
        oauth_callback_schema.lti_user.assert_called_once_with()
        assert lti_user == oauth_callback_schema.lti_user.return_value

    def test_it_returns_None_if_all_schemas_fail(
        self, bearer_token_schema, oauth_callback_schema, pyramid_request
    ):
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        oauth_callback_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        assert get_lti_user(pyramid_request) is None

    def test_it_stores_the_user(
        self, pyramid_request, user_service, bearer_token_schema
    ):
        get_lti_user(pyramid_request)

        user_service.upsert_user.assert_called_once_with(
            bearer_token_schema.lti_user.return_value
        )

    @pytest.mark.usefixtures("pyramid_request_with_identity")
    def test_it_picks_lit_user_from_identity(self, pyramid_request):
        lti_user = get_lti_user(pyramid_request, from_identity=True)

        assert lti_user == sentinel.lti_user

    @pytest.fixture
    def pyramid_request_with_identity(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy(
            userid=sentinel.userid,
            identity=Identity(sentinel.userid, sentinel.permissions, sentinel.lti_user),
        )
        return pyramid_request

    @pytest.fixture(autouse=True)
    def BearerTokenSchema(self, patch):
        return patch("lms.security.BearerTokenSchema")

    @pytest.fixture
    def bearer_token_schema(self, BearerTokenSchema):
        return BearerTokenSchema.return_value

    @pytest.fixture(autouse=True)
    def OAuthCallbackSchema(self, patch):
        return patch("lms.security.OAuthCallbackSchema")

    @pytest.fixture
    def oauth_callback_schema(self, OAuthCallbackSchema):
        return OAuthCallbackSchema.return_value


class TestGetUser:
    def test_it(self, pyramid_request, user_service, application_instance_service):
        user = _get_user(pyramid_request)

        user_service.get.assert_called_once_with(
            application_instance_service.get_current.return_value,
            pyramid_request.lti_user.user_id,
        )
        assert user == user_service.get.return_value
