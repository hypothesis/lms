from unittest import mock

import pytest
from requests import Request

from lms.services.oauth1 import OAuth1Service


class TestOAuth1Service:
    def test_we_configure_OAuth1_correctly(self, service, OAuth1, pyramid_request):
        service.get_client()

        OAuth1.assert_called_once_with(
            client_key=pyramid_request.lti_user.oauth_consumer_key,
            client_secret="TEST_SECRET",
            signature_method="HMAC-SHA1",
            signature_type="auth_header",
            force_include_body=True,
        )

    def test_we_can_be_used_to_sign_a_request(self, service, pyramid_request):
        request = Request(
            "POST",
            url="http://example.com",
            data={"param": "value"},
            auth=service.get_client(),
        )

        prepared_request = request.prepare()

        auth_header = prepared_request.headers["Authorization"].decode("iso-8859-1")

        assert auth_header.startswith("OAuth")
        assert 'oauth_version="1.0"' in auth_header
        assert (
            f'oauth_consumer_key="{pyramid_request.lti_user.oauth_consumer_key}"'
            in auth_header
        )
        assert 'oauth_signature_method="HMAC-SHA1"' in auth_header

        # This currently doesn't verify the signature, it only checks that
        # one is present.
        assert "oauth_signature=" in auth_header

    @pytest.fixture
    def service(self, context, pyramid_request):
        return OAuth1Service(context, pyramid_request)

    @pytest.fixture
    def context(self):
        # We don't use context, so it doesn't matter what it is
        return mock.sentinel.context

    @pytest.fixture
    def OAuth1(self, patch):
        return patch("lms.services.oauth1.OAuth1")


pytestmark = pytest.mark.usefixtures("ai_getter")
