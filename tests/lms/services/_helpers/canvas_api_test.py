import pytest

from lms.services._helpers.canvas_api import CanvasAPIHelper


class TestCanvasAPIHelper:
    def test_access_token_request(self, ai_getter, route_url):
        helper = CanvasAPIHelper("test_consumer_key", ai_getter, route_url)

        request = helper.access_token_request("test_authorization_code")

        ai_getter.developer_key.assert_called_once_with("test_consumer_key")
        ai_getter.developer_secret.assert_called_once_with("test_consumer_key")
        ai_getter.lms_url.assert_called_once_with("test_consumer_key")
        assert request.method == "POST"
        assert request.url == (
            "https://my-canvas-instance.com/login/oauth2/token"
            "?grant_type=authorization_code"
            "&client_id=test_developer_key"
            "&client_secret=test_developer_secret"
            "&redirect_uri=http%3A%2F%2Fexample.com%2Fcanvas_oauth_callback"
            "&code=test_authorization_code"
        )

    def test_list_files_request(self, ai_getter, route_url):
        helper = CanvasAPIHelper("test_consumer_key", ai_getter, route_url)

        request = helper.list_files_request("test_access_token", "test_course_id")

        ai_getter.lms_url.assert_called_once_with("test_consumer_key")
        assert request.method == "GET"
        assert request.headers["Authorization"] == "Bearer test_access_token"
        assert request.url == (
            "https://my-canvas-instance.com/api/v1/courses/test_course_id/files"
            "?content_types%5B%5D=application%2Fpdf"
            "&per_page=100"
        )

    def test_public_url_request(self, ai_getter, route_url):
        helper = CanvasAPIHelper("test_consumer_key", ai_getter, route_url)

        request = helper.public_url_request("test_access_token", "test_file_id")

        ai_getter.lms_url.assert_called_once_with("test_consumer_key")
        assert request.method == "GET"
        assert request.headers["Authorization"] == "Bearer test_access_token"
        assert request.url == (
            "https://my-canvas-instance.com/api/v1/files/test_file_id/public_url"
        )

    @pytest.fixture
    def ai_getter(self, ai_getter):
        ai_getter.developer_key.return_value = "test_developer_key"
        ai_getter.developer_secret.return_value = "test_developer_secret"
        ai_getter.lms_url.return_value = "https://my-canvas-instance.com/"
        return ai_getter

    @pytest.fixture
    def route_url(self, pyramid_request):
        return pyramid_request.route_url

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("canvas_oauth_callback", "/canvas_oauth_callback")
