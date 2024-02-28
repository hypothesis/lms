from unittest.mock import create_autospec, sentinel
from urllib.parse import urlencode

import pytest

from lms.services.canvas_studio import CanvasStudioService, factory
from lms.services.oauth_http import OAuthHTTPService
from tests import factories


@pytest.mark.usefixtures("aes_service", "canvas_studio_settings", "oauth_http_factory")
class TestCanvasStudioService:

    def test_get_access_token(self, svc, oauth_http_service, client_secret):
        svc.get_access_token("some_code")

        oauth_http_service.get_access_token.assert_called_with(
            "https://hypothesis.instructuremedia.com/api/public/oauth/token",
            "http://example.com/api/canvas_studio/oauth/callback",
            auth=("the_client_id", client_secret),
            authorization_code="some_code",
        )

    def test_authorization_url(self, svc):
        state = "the_callback_state"
        auth_url = svc.authorization_url(state)

        expected_query = urlencode(
            {
                "client_id": "the_client_id",
                "response_type": "code",
                "redirect_uri": svc.redirect_uri(),
                "state": state,
            }
        )

        assert (
            auth_url
            == "https://hypothesis.instructuremedia.com/api/public/oauth/authorize?"
            + expected_query
        )

    def test_redirect_uri(self, svc):
        assert (
            svc.redirect_uri() == "http://example.com/api/canvas_studio/oauth/callback"
        )

    def test_list_media_library(self, svc):
        files = svc.list_media_library()
        assert files == [
            {
                "type": "Folder",
                "display_name": "More videos",
                "updated_at": "2024-02-01",
                "id": "8",
                "contents": {
                    "path": "http://example.com/api/canvas_studio/collections/8/media"
                },
            },
            {
                "type": "File",
                "display_name": "Test video",
                "updated_at": "2024-02-03",
                "id": "canvas-studio://media/5",
            },
        ]

    def test_list_media_library_no_user_collection(self, svc, oauth_http_service):
        oauth_http_service.get.side_effect = self.get_request_handler(collections=[])
        files = svc.list_media_library()
        assert files == []

    def test_list_collection(self, svc):
        files = svc.list_collection("8")
        assert files == [
            {
                "type": "File",
                "display_name": "Another video",
                "updated_at": "2024-02-04",
                "id": "canvas-studio://media/6",
            }
        ]

    @pytest.fixture
    def svc(self, pyramid_request):
        return CanvasStudioService(pyramid_request)

    @pytest.fixture
    def oauth_http_service(self):
        svc = create_autospec(OAuthHTTPService, spec_set=True)
        svc.get.side_effect = self.get_request_handler()
        return svc

    def get_request_handler(self, collections=None):
        """Create a handler for `GET` requests to the Canvas Studio API."""

        def make_collection(id_, name, type_, created_at):
            return {"id": id_, "name": name, "type": type_, "created_at": created_at}

        def make_file(id_, title, created_at):
            return {"id": id_, "title": title, "created_at": created_at}

        if collections is None:
            # Add default collections
            collections = [
                make_collection(1, "", "user", "2024-02-01"),
                make_collection(8, "More videos", "some_type", "2024-02-01"),
            ]

        def handler(url):
            api_prefix = "https://hypothesis.instructuremedia.com/api/public/v1/"
            assert url.startswith(api_prefix)

            url_suffix = url[len(api_prefix) :]
            json_data = None

            match url_suffix:
                case "collections":
                    json_data = {
                        "collections": collections.copy(),
                    }
                case "collections/1/media":
                    json_data = {
                        "media": [
                            make_file(5, "Test video", "2024-02-03"),
                        ]
                    }
                case "collections/8/media":
                    json_data = {
                        "media": [
                            make_file(6, "Another video", "2024-02-04"),
                        ]
                    }
                case _:  # pragma: nocover
                    raise ValueError(f"Unexpected URL {url}")

            return factories.requests.Response(json_data=json_data)

        return handler

    @pytest.fixture
    def oauth_http_factory(self, oauth_http_service, patch):
        factory = patch("lms.services.canvas_studio.oauth_http_factory")
        factory.return_value = oauth_http_service
        return factory

    @pytest.fixture
    def client_secret(self, pyramid_request, aes_service):
        return pyramid_request.lti_user.application_instance.settings.get_secret(
            aes_service, "canvas_studio", "client_secret"
        )

    @pytest.fixture
    def canvas_studio_settings(self, pyramid_request, aes_service):
        application_instance = pyramid_request.lti_user.application_instance
        application_instance.settings.set("canvas_studio", "client_id", "the_client_id")
        application_instance.settings.set(
            "canvas_studio", "domain", "hypothesis.instructuremedia.com"
        )
        application_instance.settings.set_secret(
            aes_service, "canvas_studio", "client_secret", "the_client_secret"
        )


class TestFactory:
    def test_it(self, pyramid_request, CanvasStudioService):
        result = factory(sentinel.context, pyramid_request)
        CanvasStudioService.assert_called_once_with(pyramid_request)
        assert result == CanvasStudioService.return_value

    @pytest.fixture(autouse=True)
    def CanvasStudioService(self, patch):
        return patch("lms.services.canvas_studio.CanvasStudioService")
