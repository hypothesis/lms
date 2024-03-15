from unittest.mock import create_autospec, patch, sentinel
from urllib.parse import urlencode

import pytest
from h_matchers import Any

from lms.models.oauth2_token import Service
from lms.services.canvas_studio import CanvasStudioService, factory
from lms.services.exceptions import ExternalRequestError, OAuth2TokenError
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

    def test_refresh_access_token(self, svc, oauth_http_service, client_secret):
        svc.refresh_access_token()

        oauth_http_service.refresh_access_token.assert_called_with(
            "https://hypothesis.instructuremedia.com/api/public/oauth/token",
            "http://example.com/api/canvas_studio/oauth/callback",
            auth=("the_client_id", client_secret),
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

    def test_redirect_uri_localhost_workaround(self, svc, pyramid_request):
        localhost_callback = "http://localhost:8001/api/canvas_studio/oauth/callback"
        with patch.object(
            pyramid_request, "route_url", return_value=localhost_callback
        ):
            assert (
                svc.redirect_uri()
                == "https://hypothesis.local:48001/api/canvas_studio/oauth/callback"
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
                "mime_type": "video",
                "updated_at": "2024-02-03",
                "id": "canvas-studio://media/5",
            },
        ]

    def test_list_media_library_no_user_collection(self, svc, oauth_http_service):
        oauth_http_service.get.side_effect = self.get_request_handler(collections=[])
        files = svc.list_media_library()
        assert files == []

    def test_list_media_library_access_token_expired(self, svc, oauth_http_service):
        response = factories.requests.Response(status_code=401)
        oauth_http_service.get.side_effect = ExternalRequestError(response=response)

        with pytest.raises(OAuth2TokenError) as exc_info:
            svc.list_media_library()

        assert exc_info.value.refreshable is True
        assert exc_info.value.refresh_route == "canvas_studio_api.oauth.refresh"
        assert exc_info.value.refresh_service == Service.CANVAS_STUDIO

    def test_list_media_library_other_error(self, svc, oauth_http_service):
        response = factories.requests.Response(status_code=400)
        err = ExternalRequestError(response=response)
        oauth_http_service.get.side_effect = err

        with pytest.raises(ExternalRequestError) as exc_info:
            svc.list_media_library()

        assert exc_info.value == err

    def test_list_collection(self, svc):
        files = svc.list_collection("8")
        assert files == [
            {
                "type": "File",
                "display_name": "Another video",
                "mime_type": "video",
                "updated_at": "2024-02-04",
                "id": "canvas-studio://media/6",
            }
        ]

    def test_get_canonical_video_url(self, svc):
        url = svc.get_canonical_video_url("42")
        assert url == "https://hypothesis.instructuremedia.com/api/public/v1/media/42"

    def test_get_video_download_url(self, svc):
        url = svc.get_video_download_url("42")
        assert url == "https://videos.cdn.com/video.mp4?signature=abc"

    def test_get_video_download_url_error(self, svc):
        with pytest.raises(ExternalRequestError) as exc_info:
            svc.get_video_download_url("123")

        assert exc_info.value.message == "Media download did not return valid redirect"
        assert Any.instance_of(exc_info.value.response).with_attrs({"status_code": 400})

    def test_get_transcript_url_returns_url_if_published(self, svc):
        transcript_url = svc.get_transcript_url("42")
        assert (
            transcript_url == "https://hypothesis.instructuremedia.com/captions/abc.srt"
        )

    def test_get_transcript_url_returns_None_if_not_published(self, svc):
        transcript_url = svc.get_transcript_url("123")
        assert transcript_url is None

    @pytest.fixture
    def svc(self, pyramid_request):
        return CanvasStudioService(
            pyramid_request, pyramid_request.lti_user.application_instance
        )

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

        def handler(url, allow_redirects=True):
            api_prefix = "https://hypothesis.instructuremedia.com/api/public/v1/"
            assert url.startswith(api_prefix)

            url_suffix = url[len(api_prefix) :]
            json_data = None
            status_code = 200

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
                case "media/42/caption_files":
                    json_data = {
                        "caption_files": [
                            {"status": "published", "url": "captions/abc.srt"}
                        ]
                    }
                case "media/123/caption_files":
                    json_data = {
                        "caption_files": [
                            {
                                "status": "unpublished",
                            }
                        ]
                    }
                case "media/42/download":
                    assert allow_redirects is False
                    return factories.requests.Response(
                        status_code=302,
                        headers={
                            "Location": "https://videos.cdn.com/video.mp4?signature=abc"
                        },
                    )
                case "media/123/download":
                    status_code = 400
                    json_data = {}

                case _:  # pragma: nocover
                    raise ValueError(f"Unexpected URL {url}")

            return factories.requests.Response(
                status_code=status_code, json_data=json_data
            )

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
        CanvasStudioService.assert_called_once_with(
            pyramid_request, pyramid_request.lti_user.application_instance
        )
        assert result == CanvasStudioService.return_value

    @pytest.fixture(autouse=True)
    def CanvasStudioService(self, patch):
        return patch("lms.services.canvas_studio.CanvasStudioService")
