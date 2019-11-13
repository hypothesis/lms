import pytest
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.interfaces import IAuthenticationPolicy

from lms.authentication import includeme


class TestIncludeMe:
    def test_it_sets_the_authentication_policy(
        self, pyramid_config, AuthenticationPolicy
    ):
        # We need to set an authorization policy first otherwise setting an
        # authentication policy will fail (you can't have an authentication
        # policy without an authorization policy).
        pyramid_config.set_authorization_policy(ACLAuthorizationPolicy())

        includeme(pyramid_config)

        AuthenticationPolicy.assert_called_once_with("TEST_LMS_SECRET")
        assert (
            pyramid_config.registry.queryUtility(IAuthenticationPolicy)
            == AuthenticationPolicy.return_value
        )

    @pytest.fixture(autouse=True)
    def AuthenticationPolicy(self, patch):
        return patch("lms.authentication.AuthenticationPolicy")
