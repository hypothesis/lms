import pytest
from unittest import mock

from lms.services.canvas_api import CanvasAPIClient
from lms.views.api.canvas.files import FilesAPIViews


class TestListFiles:
    def test_it_gets_the_list_of_files_from_canvas(
        self, canvas_api_client, pyramid_request
    ):
        FilesAPIViews(pyramid_request).list_files()

        canvas_api_client.list_files.assert_called_once_with("test_course_id")

    def test_it_returns_the_list_of_files(self, canvas_api_client, pyramid_request):
        FilesAPIViews(
            pyramid_request
        ).list_files() == canvas_api_client.list_files.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict = {"course_id": "test_course_id"}
        return pyramid_request


class TestPublicURL:
    def test_it_gets_the_public_url_from_canvas(
        self, canvas_api_client, pyramid_request
    ):
        FilesAPIViews(pyramid_request).public_url()

        canvas_api_client.public_url.assert_called_once_with("test_file_id")

    def test_it_returns_the_public_url(self, canvas_api_client, pyramid_request):
        data = FilesAPIViews(pyramid_request).public_url()

        assert data["public_url"] == canvas_api_client.public_url.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict = {"file_id": "test_file_id"}
        return pyramid_request


@pytest.fixture(autouse=True)
def canvas_api_client(pyramid_config):
    canvas_api_client = mock.create_autospec(
        CanvasAPIClient, spec_set=True, instance=True
    )
    pyramid_config.register_service(canvas_api_client, name="canvas_api_client")
    return canvas_api_client
