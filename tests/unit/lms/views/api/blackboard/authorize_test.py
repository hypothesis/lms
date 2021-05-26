import pytest
from h_matchers import Any

from lms.services import NoOAuth2Token
from lms.views.api.blackboard.authorize import authorize, oauth2_redirect
from tests.matchers import temporary_redirect_to

pytestmark = pytest.mark.usefixtures(
    "application_instance_service", "oauth2_token_service"
)


class TestAuthorize:
    def test_it_redirects_to_the_Blackboard_authorization_page(
        self,
        application_instance_service,
        OAuthCallbackSchema,
        oauth_callback_schema,
        pyramid_request,
    ):
        application_instance = application_instance_service.get.return_value

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


class TestOAuth2Redirect:
    def test_it_saves_an_access_token_if_none_exists(
        self, pyramid_request, oauth2_token_service
    ):
        oauth2_token_service.get.side_effect = NoOAuth2Token()

        oauth2_redirect(pyramid_request)

        oauth2_token_service.save.assert_called_once_with(
            "fake_access_token", "fake_refresh_token", 9999
        )

    def test_it_doesnt_save_an_access_token_if_there_already_is_one(
        self, pyramid_request, oauth2_token_service
    ):
        oauth2_redirect(pyramid_request)

        oauth2_token_service.save.assert_not_called()

    def test_it_returns_an_empty_dict(self, pyramid_request):
        assert oauth2_redirect(pyramid_request) == {}


@pytest.fixture(autouse=True)
def OAuthCallbackSchema(patch):
    OAuthCallbackSchema = patch(
        "lms.views.api.blackboard.authorize.OAuthCallbackSchema"
    )
    return OAuthCallbackSchema


@pytest.fixture
def oauth_callback_schema(OAuthCallbackSchema):
    return OAuthCallbackSchema.return_value
