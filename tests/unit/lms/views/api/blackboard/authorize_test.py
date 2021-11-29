from unittest.mock import create_autospec

import pytest
from h_matchers import Any

from lms.resources._js_config import JSConfig
from lms.resources.oauth2_redirect import OAuth2RedirectResource
from lms.views.api.blackboard.authorize import (
    authorize,
    oauth2_redirect,
    oauth2_redirect_error,
)
from tests.matchers import temporary_redirect_to


@pytest.mark.usefixtures("application_instance_service")
class TestAuthorize:
    def test_it_redirects_to_the_Blackboard_authorization_page(
        self,
        application_instance_service,
        OAuthCallbackSchema,
        oauth_callback_schema,
        pyramid_request,
    ):
        application_instance = application_instance_service.get_current.return_value

        response = authorize(pyramid_request)

        OAuthCallbackSchema.assert_called_once_with(pyramid_request)
        assert response == temporary_redirect_to(
            Any.url(
                scheme="https",
                host=application_instance.lms_host(),
                path="learn/api/public/v1/oauth2/authorizationcode",
                query={
                    "client_id": pyramid_request.registry.settings[
                        "blackboard_api_client_id"
                    ],
                    "response_type": "code",
                    "redirect_uri": pyramid_request.route_url(
                        "blackboard_api.oauth.callback"
                    ),
                    "state": str(oauth_callback_schema.state_param.return_value),
                    "scope": "read offline",
                },
            )
        )


class TestOAuth2RedirectError:
    def test_it(self, pyramid_request):
        template_variables = oauth2_redirect_error(pyramid_request)

        pyramid_request.context.js_config.enable_oauth2_redirect_error_mode.assert_called_once_with(
            error_code=None,
            auth_route="blackboard_api.oauth.authorize",
        )
        assert not template_variables

    def test_missing_integration_error(self, pyramid_request):
        pyramid_request.params = {
            "error_description": "Application not enabled for site"
        }

        template_variables = oauth2_redirect_error(pyramid_request)

        pyramid_request.context.js_config.enable_oauth2_redirect_error_mode.assert_called_once_with(
            error_code=JSConfig.ErrorCode.BLACKBOARD_MISSING_INTEGRATION,
            auth_route="blackboard_api.oauth.authorize",
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


@pytest.mark.usefixtures("blackboard_api_client")
class TestOAuth2Redirect:
    def test_it_gets_a_new_access_token_for_the_user(
        self, pyramid_request, blackboard_api_client
    ):
        pyramid_request.params["code"] = "test_code"

        result = oauth2_redirect(pyramid_request)

        blackboard_api_client.get_token.assert_called_once_with("test_code")
        assert not result


@pytest.fixture(autouse=True)
def OAuthCallbackSchema(patch):
    OAuthCallbackSchema = patch(
        "lms.views.api.blackboard.authorize.OAuthCallbackSchema"
    )
    return OAuthCallbackSchema


@pytest.fixture
def oauth_callback_schema(OAuthCallbackSchema):
    return OAuthCallbackSchema.return_value
