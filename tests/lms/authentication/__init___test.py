import pytest
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid import testing
from pyramid.interfaces import IAuthenticationPolicy

from lms.authentication import includeme


class TestIncludeMe:
    def test_it_sets_the_authentication_policy(
        self, groupfinder, pyramid_config, AuthTktAuthenticationPolicy
    ):
        # We need to set an authorization policy first otherwise setting an
        # authentication policy will fail (you can't have an authentication
        # policy without an authorization policy).
        pyramid_config.set_authorization_policy(ACLAuthorizationPolicy())

        includeme(pyramid_config)

        AuthTktAuthenticationPolicy.assert_called_once_with(
            "TEST_LMS_SECRET", callback=groupfinder, hashalg="sha512"
        )
        assert (
            pyramid_config.registry.queryUtility(IAuthenticationPolicy)
            == AuthTktAuthenticationPolicy.return_value
        )

    @pytest.fixture(autouse=True)
    def AuthTktAuthenticationPolicy(self, patch):
        return patch("lms.authentication.AuthTktAuthenticationPolicy")

    @pytest.fixture(autouse=True)
    def groupfinder(self, patch):
        return patch("lms.authentication.groupfinder")
