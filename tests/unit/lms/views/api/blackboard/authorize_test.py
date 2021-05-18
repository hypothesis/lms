from urllib.parse import parse_qs, urlparse

import pytest

from lms.services import NoOAuth2Token
from lms.views.api.blackboard.authorize import authorize, oauth2_redirect

pytestmark = pytest.mark.usefixtures("oauth2_token_service")


class TestAuthorize:
    def test_it_just_redirects_to_the_oauth2_redirect_view(self, pyramid_request):
        response = authorize(pyramid_request)

        assert response.status_int == 302
        assert response.location.startswith(
            pyramid_request.route_url("blackboard_api.oauth.callback")
        )

    def test_it_authenticates_the_redirect_with_an_OAuth2_state_param(
        self, pyramid_request, OAuthCallbackSchema
    ):
        response = authorize(pyramid_request)

        OAuthCallbackSchema.assert_called_once_with(pyramid_request)
        state = parse_qs(urlparse(response.location).query).get("state")
        assert state == ["test_state"]


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
    OAuthCallbackSchema.return_value.state_param.return_value = "test_state"
    return OAuthCallbackSchema
