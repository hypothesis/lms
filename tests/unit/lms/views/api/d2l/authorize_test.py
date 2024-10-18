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
    @pytest.mark.parametrize(
        "groups,files,scopes",
        [
            (False, True, "content:toc:read content:topics:read content:file:read"),
            (True, False, "groups:group:read"),
            (
                True,
                True,
                "content:toc:read content:topics:read content:file:read groups:group:read",
            ),
        ],
    )
    def test_it(
        self,
        OAuthCallbackSchema,
        oauth_callback_schema,
        pyramid_request,
        groups,
        files,
        scopes,
    ):
        ai = create_autospec(ApplicationInstance)
        pyramid_request.lti_user.application_instance = ai
        ai.settings.get.return_value = "CLIENT_ID"
        oauth_callback_schema.state_param.return_value = "STATE"
        pyramid_request.product.settings.groups_enabled = groups
        pyramid_request.product.settings.files_enabled = files

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
                    "scope": scopes,
                },
            )
        )

    def test_raises_with_no_scopes(self, pyramid_request):
        pyramid_request.product.settings.groups_enabled = False
        pyramid_request.product.settings.files_enabled = False

        with pytest.raises(NotImplementedError):
            authorize(pyramid_request)


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
    return patch("lms.views.api.d2l.authorize.OAuthCallbackSchema")


@pytest.fixture
def oauth_callback_schema(OAuthCallbackSchema):
    return OAuthCallbackSchema.return_value
