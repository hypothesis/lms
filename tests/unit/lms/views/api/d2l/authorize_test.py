from unittest.mock import create_autospec

import pytest
from h_matchers import Any

from lms.models import ApplicationInstance
from lms.resources._js_config import JSConfig
from lms.resources.oauth2_redirect import OAuth2RedirectResource
from lms.views.api.d2l.authorize import (
    authorize,
    oauth2_redirect,
    oauth2_redirect_error,
)
from tests.matchers import temporary_redirect_to


@pytest.mark.usefixtures("application_instance_service")
class TestAuthorize:
    def test_it(
        self,
        application_instance_service,
        OAuthCallbackSchema,
        oauth_callback_schema,
        pyramid_request,
    ):
        ai = create_autospec(ApplicationInstance)
        application_instance_service.get_current.return_value = ai
        ai.settings.get.return_value = "CLIENT_ID"
        oauth_callback_schema.state_param.return_value = "STATE"

        response = authorize(pyramid_request)

        OAuthCallbackSchema.assert_called_once_with(pyramid_request)
        ai.settings.get.assert_called_once_with("desire2learn", "client_id")
        assert response == temporary_redirect_to(
            Any.url(
                scheme="https",
                host="auth.brightspace.com",
                path="oauth2/auth",
                query={
                    "client_id": "CLIENT_ID",
                    "response_type": "code",
                    "redirect_uri": pyramid_request.route_url("d2l_api.oauth.callback"),
                    "state": "STATE",
                    "scope": "core:*:* groups:*:*",
                },
            )
        )


class TestOAuth2Redirect:
    def test_it(self, pyramid_request, d2l_api_client):
        pyramid_request.params["code"] = "test_code"

        result = oauth2_redirect(pyramid_request)

        d2l_api_client.get_token.assert_called_once_with("test_code")
        assert not result


class TestOAuth2RedirectError:
    def test_it(self, pyramid_request):
        template_variables = oauth2_redirect_error(pyramid_request)

        pyramid_request.context.js_config.enable_oauth2_redirect_error_mode.assert_called_once_with(
            auth_route="d2l_api.oauth.authorize"
        )
        assert not template_variables

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        js_config.ErrorCode = JSConfig.ErrorCode
        pyramid_request.context = create_autospec(
            OAuth2RedirectResource,
            instance=True,
            js_config=js_config,
        )
        return pyramid_request


@pytest.fixture(autouse=True)
def OAuthCallbackSchema(patch):
    OAuthCallbackSchema = patch("lms.views.api.d2l.authorize.OAuthCallbackSchema")
    return OAuthCallbackSchema


@pytest.fixture
def oauth_callback_schema(OAuthCallbackSchema):
    return OAuthCallbackSchema.return_value
