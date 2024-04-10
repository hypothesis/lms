from unittest.mock import create_autospec, patch, sentinel
from urllib.parse import urlencode

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPBadRequest
from requests import RequestException

from lms.models.oauth2_token import Service
from lms.services.canvas_studio import CanvasStudioService, factory
from lms.services.exceptions import ExternalRequestError, OAuth2TokenError
from lms.services.oauth_http import OAuthHTTPService
from tests import factories


@pytest.mark.usefixtures(
    "aes_service", "canvas_studio_settings", "oauth_http_factory", "admin_user"
)
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
                "thumbnail_url": None,
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
                "thumbnail_url": "https://videos.cdn.com/thumbnails/6.jpg",
            }
        ]

    def test_get_canonical_video_url(self, svc):
        url = svc.get_canonical_video_url("42")
        assert url == "https://hypothesis.instructuremedia.com/api/public/v1/media/42"

    def test_get_video_download_url(self, svc):
        url = svc.get_video_download_url("42")
        assert url == "https://videos.cdn.com/video.mp4?signature=abc"

    def test_get_video_download_url_as_admin(
        self,
        svc,
        pyramid_request,
        admin_user,
        oauth_http_service,
        admin_oauth_http_service,
    ):
        pyramid_request.lti_user = admin_user
        oauth_http_service.get.side_effect = self.get_request_handler(is_admin=True)

        url = svc.get_video_download_url("42")

        # When the current user _is_ the admin, we use the normal/default
        # OAuthHTTPService instead of the separate admin one.
        oauth_http_service.get.assert_called_once()
        admin_oauth_http_service.get.assert_not_called()
        assert url == "https://videos.cdn.com/video.mp4?signature=abc"

    def test_get_video_download_non_redirect(self, svc):
        with pytest.raises(ExternalRequestError) as exc_info:
            svc.get_video_download_url("123")

        assert exc_info.value.message == "Media download did not return valid redirect"
        assert Any.instance_of(exc_info.value.response).with_attrs({"status_code": 400})

    def test_get_video_download_error(self, svc):
        with pytest.raises(ExternalRequestError) as exc_info:
            svc.get_video_download_url("456")
        assert Any.instance_of(exc_info.value.response).with_attrs({"status_code": 404})

    def test_get_video_download_url_fails_if_admin_email_not_set(
        self, svc, pyramid_request
    ):
        pyramid_request.lti_user.application_instance.settings.set(
            "canvas_studio", "admin_email", None
        )
        with pytest.raises(HTTPBadRequest) as exc_info:
            svc.get_video_download_url("42")
        assert (
            exc_info.value.message
            == "Admin account is not configured for Canvas Studio integration"
        )

    # Test scenario where the admin user never performed an LTI launch, and thus
    # we cannot look up the admin email <-> LTI user ID association.
    def test_get_video_download_url_fails_if_admin_user_not_in_db(
        self, svc, admin_user, db_session
    ):
        db_session.flush()  # Ensure admin user is saved to DB
        db_session.delete(admin_user)

        with pytest.raises(HTTPBadRequest) as exc_info:
            svc.get_video_download_url("42")

        assert (
            exc_info.value.message
            == "The Canvas Studio admin needs to authenticate the Hypothesis integration"
        )

    # Test scenario where the admin user has performed an LTI launch, but has
    # not authenticated with Canvas Studio or the token has clearly expired.
    def test_get_video_download_url_fails_if_admin_not_authenticated(
        self, svc, admin_oauth_http_service
    ):
        admin_oauth_http_service.get.side_effect = OAuth2TokenError()

        with pytest.raises(HTTPBadRequest) as exc_info:
            svc.get_video_download_url("42")

        assert (
            exc_info.value.message
            == "The Canvas Studio admin needs to authenticate the Hypothesis integration"
        )

    def test_admin_token_refreshed_if_needed(
        self, admin_oauth_http_service, svc, client_secret
    ):
        # Set up admin-authenticated OAuth request to fail due to expired token.
        token_expired_response = factories.requests.Response(status_code=401)
        original_get = admin_oauth_http_service.get.side_effect
        admin_oauth_http_service.get.side_effect = ExternalRequestError(
            response=token_expired_response
        )

        def refresh_ok(*_args, **_kwargs):
            admin_oauth_http_service.get.side_effect = original_get

        def refresh_fail(*_args, **_kwargs):
            raise ExternalRequestError(message="refresh failed")

        admin_oauth_http_service.refresh_access_token.side_effect = refresh_ok

        # Perform a request that is admin-authenticated. This should trigger
        # a refresh and then succeed as normal.
        url = svc.get_video_download_url("42")

        admin_oauth_http_service.refresh_access_token.assert_called_with(
            "https://hypothesis.instructuremedia.com/api/public/oauth/token",
            "http://example.com/api/canvas_studio/oauth/callback",
            auth=("the_client_id", client_secret),
        )
        assert url == "https://videos.cdn.com/video.mp4?signature=abc"

        # Set up the initial request to fail again, due to an expired token,
        # but this time make the refresh fail.
        admin_oauth_http_service.get.side_effect = ExternalRequestError(
            response=token_expired_response
        )
        admin_oauth_http_service.refresh_access_token.side_effect = refresh_fail

        with pytest.raises(ExternalRequestError) as exc_info:
            svc.get_video_download_url("42")

        assert (
            exc_info.value.message
            == "Canvas Studio admin token refresh failed. Ask the admin user to re-authenticate."
        )

        # Set up the initial request to fail again, due to an expired token,
        # but this time make subsequent requests fail even though the refresh
        # apparently succeeded.
        admin_oauth_http_service.get.side_effect = ExternalRequestError(
            response=token_expired_response
        )
        admin_oauth_http_service.refresh_access_token.side_effect = None

        with pytest.raises(Exception) as exc_info:
            svc.get_video_download_url("42")

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

    @pytest.fixture
    def admin_oauth_http_service(self):
        svc = create_autospec(OAuthHTTPService, spec_set=True)
        svc.get.side_effect = self.get_request_handler(is_admin=True)
        return svc

    def get_request_handler(self, collections=None, is_admin=False):
        """
        Create a handler for `GET` requests to the Canvas Studio API.

        :param collections: The list of collections the user can access
        :param is_admin: Whether to simulate being the admin user
        """

        def make_collection(id_, name, type_, created_at):
            return {"id": id_, "name": name, "type": type_, "created_at": created_at}

        def make_file(id_, title, created_at, with_thumbnail=False):
            file = {"id": id_, "title": title, "created_at": created_at}
            if with_thumbnail:
                file["thumbnail_url"] = f"https://videos.cdn.com/thumbnails/{id_}.jpg"
            return file

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
                            make_file(
                                6, "Another video", "2024-02-04", with_thumbnail=True
                            ),
                        ]
                    }
                case "media/42/caption_files":
                    assert is_admin
                    json_data = {
                        "caption_files": [
                            {"status": "published", "url": "captions/abc.srt"}
                        ]
                    }
                case "media/123/caption_files":
                    assert is_admin
                    json_data = {
                        "caption_files": [
                            {
                                "status": "unpublished",
                            }
                        ]
                    }
                case "media/42/download":
                    assert is_admin
                    assert allow_redirects is False
                    return factories.requests.Response(
                        status_code=302,
                        headers={
                            "Location": "https://videos.cdn.com/video.mp4?signature=abc"
                        },
                    )
                case "media/123/download":
                    # This shouldn't happen, but it simulates what would happen
                    # if we received a non-4xx/5xx status code that is not a
                    # redirect.
                    status_code = 200
                    json_data = {}
                case "media/456/download":
                    status_code = 404
                    json_data = {}

                case _:  # pragma: nocover
                    raise ValueError(f"Unexpected URL {url}")

            # This mirrors how HTTPService handles responses based on status code.
            response = None
            try:
                response = factories.requests.Response(
                    status_code=status_code, json_data=json_data
                )
                response.raise_for_status()
                return response
            except RequestException as err:
                raise ExternalRequestError(
                    request=err.request, response=response
                ) from err

        return handler

    @pytest.fixture
    def oauth_http_factory(self, oauth_http_service, admin_oauth_http_service, patch):
        factory = patch("lms.services.canvas_studio.oauth_http_factory")

        def create_oauth_http_service(_context, _request, service, user_id=None):
            assert service is Service.CANVAS_STUDIO
            if user_id == "admin_user_id":
                return admin_oauth_http_service
            return oauth_http_service

        factory.side_effect = create_oauth_http_service
        return factory

    @pytest.fixture
    def client_secret(self, pyramid_request, aes_service):
        return pyramid_request.lti_user.application_instance.settings.get_secret(
            aes_service, "canvas_studio", "client_secret"
        )

    @pytest.fixture
    def canvas_studio_settings(self, pyramid_request, aes_service):
        application_instance = pyramid_request.lti_user.application_instance
        application_instance.settings.set(
            "canvas_studio", "admin_email", "admin@hypothesis.edu"
        )
        application_instance.settings.set("canvas_studio", "client_id", "the_client_id")
        application_instance.settings.set(
            "canvas_studio", "domain", "hypothesis.instructuremedia.com"
        )
        application_instance.settings.set_secret(
            aes_service, "canvas_studio", "client_secret", "the_client_secret"
        )

    @pytest.fixture
    def admin_user(self, db_session, pyramid_request):
        user = factories.User(
            email="admin@hypothesis.edu",
            user_id="admin_user_id",
            application_instance=pyramid_request.lti_user.application_instance,
        )
        db_session.add(user)
        return user


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
