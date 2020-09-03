from unittest.mock import sentinel

import pytest

from lms.services.canvas_api.factory import canvas_api_client_factory


class TestCanvasAPIClientFactory:
    def test_building_the_CanvasAPIClient(
        self, pyramid_request, CanvasAPIClient, AuthenticatedClient
    ):
        canvas_api = canvas_api_client_factory(sentinel.context, pyramid_request)

        CanvasAPIClient.assert_called_once_with(AuthenticatedClient.return_value)
        assert canvas_api == CanvasAPIClient.return_value

    def test_building_the_BasicClient(self, pyramid_request, BasicClient, ai_getter):
        ai_getter.lms_url.return_value = "https://example.com/path"

        canvas_api_client_factory(sentinel.context, pyramid_request)

        BasicClient.assert_called_once_with("example.com")

    def test_building_the_AuthenticatedClient(
        self,
        pyramid_request,
        ai_getter,
        AuthenticatedClient,
        BasicClient,
        token_store_service,
    ):
        canvas_api_client_factory(sentinel.context, pyramid_request)

        AuthenticatedClient.assert_called_once_with(
            basic_client=BasicClient.return_value,
            token_store=token_store_service,
            client_id=ai_getter.developer_key(),
            client_secret=ai_getter.developer_secret(),
            redirect_uri=pyramid_request.route_url("canvas_oauth_callback"),
        )

    @pytest.fixture(autouse=True)
    def BasicClient(self, patch):
        return patch("lms.services.canvas_api.factory.BasicClient")

    @pytest.fixture(autouse=True)
    def AuthenticatedClient(self, patch):
        return patch("lms.services.canvas_api.factory.AuthenticatedClient")

    @pytest.fixture(autouse=True)
    def CanvasAPIClient(self, patch):
        return patch("lms.services.canvas_api.factory.CanvasAPIClient")


pytestmark = pytest.mark.usefixtures("ai_getter", "token_store_service")
