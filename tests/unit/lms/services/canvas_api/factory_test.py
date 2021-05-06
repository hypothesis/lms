from unittest.mock import sentinel

import pytest

from lms.services.canvas_api.factory import canvas_api_client_factory

pytestmark = pytest.mark.usefixtures(
    "application_instance_service", "oauth2_token_service"
)


class TestCanvasAPIClientFactory:
    def test_building_the_CanvasAPIClient(
        self, pyramid_request, CanvasAPIClient, AuthenticatedClient
    ):
        canvas_api = canvas_api_client_factory(sentinel.context, pyramid_request)

        CanvasAPIClient.assert_called_once_with(AuthenticatedClient.return_value)
        assert canvas_api == CanvasAPIClient.return_value

    def test_building_the_BasicClient(
        self, pyramid_request, BasicClient, application_instance_service
    ):
        application_instance_service.get.return_value.lms_url = (
            "https://example.com/path"
        )

        canvas_api_client_factory(sentinel.context, pyramid_request)

        BasicClient.assert_called_once_with("example.com")

    def test_building_the_AuthenticatedClient(
        self,
        pyramid_request,
        application_instance_service,
        AuthenticatedClient,
        BasicClient,
        oauth2_token_service,
    ):
        canvas_api_client_factory(sentinel.context, pyramid_request)

        application_instance_service.get.return_value.decrypted_developer_secret.assert_called_once_with(
            pyramid_request.registry.settings["aes_secret"]
        )

        AuthenticatedClient.assert_called_once_with(
            basic_client=BasicClient.return_value,
            oauth2_token_service=oauth2_token_service,
            client_id=application_instance_service.get.return_value.developer_key,
            client_secret=application_instance_service.get.return_value.decrypted_developer_secret.return_value,
            redirect_uri=pyramid_request.route_url("canvas_api.oauth.callback"),
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
