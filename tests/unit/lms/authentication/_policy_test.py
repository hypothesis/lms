from unittest import mock

import pytest

from lms.authentication._policy import AuthenticationPolicy


class TestAuthenticationPolicy:
    @pytest.mark.parametrize(
        "method_name",
        ("authenticated_userid", "unauthenticated_userid", "effective_principals"),
    )
    def test_it_returns_the_userid_from_LTIAuthenticationPolicy(
        self, method_name, policy, LTIAuthenticationPolicy, lti_authentication_policy
    ):
        method = getattr(policy, method_name)

        user_id = method(mock.sentinel.request)

        LTIAuthenticationPolicy.assert_called_once_with()
        lti_authentication_policy_method = getattr(
            lti_authentication_policy, method_name
        )
        lti_authentication_policy_method.assert_called_with(mock.sentinel.request)
        assert user_id == lti_authentication_policy_method.return_value

    @pytest.mark.parametrize(
        "method_name",
        ("authenticated_userid", "unauthenticated_userid", "effective_principals"),
    )
    def test_it_falls_back_on_AuthTktAuthenticationPolicy_if_theres_no_LTI_user(
        self,
        AuthTktAuthenticationPolicy,
        auth_tkt_authentication_policy,
        groupfinder,
        lti_authentication_policy,
        method_name,
        policy,
    ):
        lti_authentication_policy.authenticated_userid.return_value = None
        method = getattr(policy, method_name)

        user_id = method(mock.sentinel.request)

        AuthTktAuthenticationPolicy.assert_called_once_with(
            "TEST_SECRET", groupfinder, hashalg="sha512"
        )
        auth_tkt_authentication_policy_method = getattr(
            auth_tkt_authentication_policy, method_name
        )
        auth_tkt_authentication_policy_method.assert_called_once_with(
            mock.sentinel.request
        )
        assert user_id == auth_tkt_authentication_policy_method.return_value

    def test_remember_delegates_to_LTIAuthenticationPolicy(
        self,
        policy,
        LTIAuthenticationPolicy,
        lti_authentication_policy,
        auth_tkt_authentication_policy,
    ):
        policy.remember(
            mock.sentinel.request, mock.sentinel.userid, kwarg=mock.sentinel.kwarg
        )

        LTIAuthenticationPolicy.assert_called_once_with()
        lti_authentication_policy.remember.assert_called_once_with(
            mock.sentinel.request, mock.sentinel.userid, kwarg=mock.sentinel.kwarg
        )
        auth_tkt_authentication_policy.remember.assert_not_called()

    def test_remember_falls_back_on_AuthTktAuthenticationPolicy(
        self, policy, lti_authentication_policy, auth_tkt_authentication_policy
    ):
        lti_authentication_policy.authenticated_userid.return_value = None

        policy.remember(
            mock.sentinel.request, mock.sentinel.userid, kwarg=mock.sentinel.kwarg
        )
        auth_tkt_authentication_policy.remember.assert_called_once_with(
            mock.sentinel.request, mock.sentinel.userid, kwarg=mock.sentinel.kwarg
        )
        lti_authentication_policy.remember.assert_not_called()

    def test_forget_delegates_to_LTIAuthenticationPolicy(
        self,
        policy,
        LTIAuthenticationPolicy,
        lti_authentication_policy,
        auth_tkt_authentication_policy,
    ):
        policy.forget(mock.sentinel.request)

        LTIAuthenticationPolicy.assert_called_once_with()
        lti_authentication_policy.forget.assert_called_once_with(mock.sentinel.request)
        auth_tkt_authentication_policy.forget.assert_not_called()

    def test_forget_falls_back_on_AuthTktAuthenticationPolicy(
        self, policy, lti_authentication_policy, auth_tkt_authentication_policy
    ):
        lti_authentication_policy.authenticated_userid.return_value = None

        policy.forget(mock.sentinel.request)
        auth_tkt_authentication_policy.forget.assert_called_once_with(
            mock.sentinel.request
        )
        lti_authentication_policy.forget.assert_not_called()

    @pytest.fixture
    def policy(self):
        return AuthenticationPolicy("TEST_SECRET")


@pytest.fixture(autouse=True)
def AuthTktAuthenticationPolicy(patch):
    return patch("lms.authentication._policy.AuthTktAuthenticationPolicy")


@pytest.fixture
def auth_tkt_authentication_policy(AuthTktAuthenticationPolicy):
    return AuthTktAuthenticationPolicy.return_value


@pytest.fixture(autouse=True)
def LTIAuthenticationPolicy(patch):
    return patch("lms.authentication._policy.LTIAuthenticationPolicy")


@pytest.fixture
def lti_authentication_policy(LTIAuthenticationPolicy):
    return LTIAuthenticationPolicy.return_value


@pytest.fixture(autouse=True)
def groupfinder(patch):
    return patch("lms.authentication._policy.groupfinder")
