import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPForbidden, HTTPFound

from lms.views.lti.oidc import oidc_view


class TestOIDC:
    def test_missing_registration(self, lti_registration, pyramid_request):
        lti_registration.get.return_value = None

        with pytest.raises(HTTPForbidden):
            oidc_view(pyramid_request)

        lti_registration.get.assert_called_once_with(
            issuer=pyramid_request.parsed_params["iss"],
            client_id=pyramid_request.parsed_params["client_id"],
        )

    def test_it(self, lti_registration, pyramid_request):
        lti_registration.get.return_value.auth_login_url = (
            "https://lms.com/auth_login_url"
        )

        result = oidc_view(pyramid_request)

        assert isinstance(result, HTTPFound)
        assert result.location == Any.url(
            host="lms.com",
            path="auth_login_url",
            query={
                "scope": "openid",
                "response_type": "id_token",
                "response_mode": "form_post",
                "prompt": "none",
                "login_hint": pyramid_request.parsed_params["login_hint"],
                "lti_message_hint": pyramid_request.parsed_params["lti_message_hint"],
                "client_id": pyramid_request.parsed_params["client_id"],
                "state": Any(),
                "nonce": Any(),
                "redirect_uri": pyramid_request.parsed_params["target_link_uri"],
            },
        )
        lti_registration.get.assert_called_once_with(
            pyramid_request.parsed_params["iss"],
            pyramid_request.parsed_params["client_id"],
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "iss": "https://lms.com",
            "client_id": "CLIENT_ID",
            "target_link_uri": "http://lms.com/target_link_uri",
            "login_hint": "LOGIN_HINT",
            "lti_message_hint": "LTI_MESSAGE_HINT",
        }
        return pyramid_request
