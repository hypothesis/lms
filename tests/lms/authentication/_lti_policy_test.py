import pytest
from unittest import mock

from pyramid import security

from lms.authentication._lti_policy import LTIAuthenticationPolicy


class TestLTIAuthenticationPolicy:
    @pytest.mark.parametrize(
        "method_name", ["authenticated_userid", "unauthenticated_userid"]
    )
    def test_it_returns_the_lti_userid(self, method_name, pyramid_request, _helpers):
        policy = LTIAuthenticationPolicy()
        method = getattr(policy, method_name)

        userid = policy.authenticated_userid(pyramid_request)

        _helpers.authenticated_userid.assert_called_once_with(pyramid_request.lti_user)
        assert userid == _helpers.authenticated_userid.return_value

    @pytest.mark.parametrize(
        "method_name", ["authenticated_userid", "unauthenticated_userid"]
    )
    def test_it_returns_None_if_theres_no_lti_user(self, method_name, pyramid_request):
        pyramid_request.lti_user = None
        policy = LTIAuthenticationPolicy()
        method = getattr(policy, method_name)

        assert policy.authenticated_userid(pyramid_request) is None

    def test_effective_principals_when_theres_an_lti_user(
        self, pyramid_request, _helpers
    ):
        policy = LTIAuthenticationPolicy()

        principals = policy.effective_principals(pyramid_request)

        _helpers.authenticated_userid.assert_called_once_with(pyramid_request.lti_user)
        assert principals == [
            security.Everyone,
            security.Authenticated,
            _helpers.authenticated_userid.return_value,
        ]

    def test_effective_principals_when_theres_no_lti_user(
        self, pyramid_request, _helpers
    ):
        pyramid_request.lti_user = None
        policy = LTIAuthenticationPolicy()

        principals = policy.effective_principals(pyramid_request)

        _helpers.authenticated_userid.assert_not_called()
        assert principals == [security.Everyone]

    def test_remember(self, pyramid_request):
        LTIAuthenticationPolicy().remember(
            pyramid_request, "TEST_USERID", kwarg=mock.sentinel.kwarg
        )

    def test_forget(self, pyramid_request):
        LTIAuthenticationPolicy().forget(pyramid_request)


@pytest.fixture(autouse=True)
def _helpers(patch):
    return patch("lms.authentication._lti_policy._helpers")
