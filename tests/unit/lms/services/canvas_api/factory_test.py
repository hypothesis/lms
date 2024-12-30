from unittest.mock import sentinel

import pytest

from lms.services.canvas_api.factory import canvas_api_client_factory
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "application_instance_service", "oauth2_token_service", "file_service"
)


class TestCanvasAPIClientFactory:
    @pytest.mark.usefixtures("aes_service")
    @pytest.mark.parametrize("folders_enabled", [True, False])
    def test_it(
        self,
        pyramid_request,
        CanvasAPIClient,
        AuthenticatedClient,
        BasicClient,
        CanvasPagesClient,
        oauth2_token_service,
        file_service,
        folders_enabled,
        application_instance,
        aes_service,
    ):
        application_instance.settings.set("canvas", "folders_enabled", folders_enabled)

        canvas_api = canvas_api_client_factory(sentinel.context, pyramid_request)

        BasicClient.assert_called_once_with(application_instance.lms_host())
        CanvasPagesClient.assert_called_once_with(
            AuthenticatedClient.return_value, file_service
        )
        CanvasAPIClient.assert_called_once_with(
            AuthenticatedClient.return_value,
            file_service=file_service,
            pages_client=CanvasPagesClient.return_value,
            folders_enabled=folders_enabled,
        )
        AuthenticatedClient.assert_called_once_with(
            basic_client=BasicClient.return_value,
            oauth2_token_service=oauth2_token_service,
            client_id=application_instance.developer_key,
            client_secret=application_instance.decrypted_developer_secret(aes_service),
            redirect_uri=pyramid_request.route_url("canvas_api.oauth.callback"),
        )

        assert canvas_api == CanvasAPIClient.return_value

    def test_it_with_application_instance_and_user_id(
        self,
        pyramid_request,
        CanvasAPIClient,
        AuthenticatedClient,
        BasicClient,
        CanvasPagesClient,
        aes_service,
        file_service_factory,
        oauth2_token_service_factory,
    ):
        application_instance = factories.ApplicationInstance()

        canvas_api = canvas_api_client_factory(
            sentinel.context,
            pyramid_request,
            application_instance=application_instance,
            user_id=sentinel.user_id,
        )

        BasicClient.assert_called_once_with(application_instance.lms_host())
        CanvasPagesClient.assert_called_once_with(
            AuthenticatedClient.return_value, file_service_factory.return_value
        )
        CanvasAPIClient.assert_called_once_with(
            AuthenticatedClient.return_value,
            file_service=file_service_factory.return_value,
            pages_client=CanvasPagesClient.return_value,
            folders_enabled=False,
        )
        AuthenticatedClient.assert_called_once_with(
            basic_client=BasicClient.return_value,
            oauth2_token_service=oauth2_token_service_factory.return_value,
            client_id=application_instance.developer_key,
            client_secret=application_instance.decrypted_developer_secret(aes_service),
            redirect_uri=pyramid_request.route_url("canvas_api.oauth.callback"),
        )

        assert canvas_api == CanvasAPIClient.return_value

    @pytest.fixture(autouse=True)
    def BasicClient(self, patch):
        return patch("lms.services.canvas_api.factory.BasicClient")

    @pytest.fixture(autouse=True)
    def AuthenticatedClient(self, patch):
        return patch("lms.services.canvas_api.factory.AuthenticatedClient")

    @pytest.fixture(autouse=True)
    def CanvasPagesClient(self, patch):
        return patch("lms.services.canvas_api.factory.CanvasPagesClient")

    @pytest.fixture(autouse=True)
    def CanvasAPIClient(self, patch):
        return patch("lms.services.canvas_api.factory.CanvasAPIClient")

    @pytest.fixture(autouse=True)
    def file_service_factory(self, patch):
        return patch("lms.services.canvas_api.factory.file_service_factory")

    @pytest.fixture(autouse=True)
    def oauth2_token_service_factory(self, patch):
        return patch("lms.services.canvas_api.factory.oauth2_token_service_factory")
