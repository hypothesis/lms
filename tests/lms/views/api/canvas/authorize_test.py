from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest

from lms.views.api.canvas.authorize import CanvasAPIAuthorizeViews
from lms.services.canvas_api import CanvasAPIClient


class TestAuthorize:
    def test_it_redirects_to_the_right_Canvas_endpoint(
        self, ai_getter, pyramid_request
    ):
        response = CanvasAPIAuthorizeViews(pyramid_request).authorize()

        assert response.status_code == 302
        ai_getter.lms_url.assert_called_once_with(
            pyramid_request.lti_user.oauth_consumer_key
        )
        assert response.location.startswith(
            f"{ai_getter.lms_url.return_value}/login/oauth2/auth"
        )

    def test_it_includes_the_client_id_in_a_query_param(
        self, ai_getter, pyramid_request
    ):
        response = CanvasAPIAuthorizeViews(pyramid_request).authorize()

        query_params = parse_qs(urlparse(response.location).query)

        ai_getter.developer_key.assert_called_once_with(
            pyramid_request.lti_user.oauth_consumer_key
        )
        assert query_params["client_id"] == [str(ai_getter.developer_key.return_value)]

    def test_it_includes_the_response_type_in_a_query_param(self, pyramid_request):
        response = CanvasAPIAuthorizeViews(pyramid_request).authorize()

        query_params = parse_qs(urlparse(response.location).query)

        assert query_params["response_type"] == ["code"]

    def test_it_includes_the_redirect_uri_in_a_query_param(self, pyramid_request):
        response = CanvasAPIAuthorizeViews(pyramid_request).authorize()

        query_params = parse_qs(urlparse(response.location).query)

        assert query_params["redirect_uri"] == [
            "http://example.com/canvas_oauth_callback"
        ]

    def test_it_includes_the_state_in_a_query_param(
        self, pyramid_request, CanvasOAuthCallbackSchema, canvas_oauth_callback_schema
    ):
        response = CanvasAPIAuthorizeViews(pyramid_request).authorize()

        query_params = parse_qs(urlparse(response.location).query)

        CanvasOAuthCallbackSchema.assert_called_once_with(pyramid_request)
        canvas_oauth_callback_schema.state_param.assert_called_once_with()
        assert query_params["state"] == [
            canvas_oauth_callback_schema.state_param.return_value
        ]


class TestOAuth2Redirect:
    def test_it_gets_an_access_token_from_canvas(
        self, canvas_api_client, pyramid_request
    ):
        pyramid_request.parsed_params = {"code": "test_authorization_code"}

        CanvasAPIAuthorizeViews(pyramid_request).oauth2_redirect()

        canvas_api_client.get_token.assert_called_once_with("test_authorization_code")

    def test_it_saves_the_access_token_to_the_db(
        self, canvas_api_client, pyramid_request
    ):
        pyramid_request.parsed_params = {"code": "test_authorization_code"}

        CanvasAPIAuthorizeViews(pyramid_request).oauth2_redirect()

        canvas_api_client.save_token.assert_called_once_with(
            *canvas_api_client.get_token.return_value
        )


@pytest.fixture(autouse=True)
def canvas_api_client(pyramid_config):
    canvas_api_client = mock.create_autospec(
        CanvasAPIClient, spec_set=True, instance=True
    )
    canvas_api_client.get_token.return_value = (
        "test_access_token",
        "test_refresh_token",
        3600,
    )
    pyramid_config.register_service(canvas_api_client, name="canvas_api_client")
    return canvas_api_client


@pytest.fixture(autouse=True)
def CanvasOAuthCallbackSchema(patch):
    return patch("lms.views.api.canvas.authorize.CanvasOAuthCallbackSchema")


@pytest.fixture
def canvas_oauth_callback_schema(CanvasOAuthCallbackSchema):
    schema = CanvasOAuthCallbackSchema.return_value
    schema.state_param.return_value = "test_state"
    return schema
