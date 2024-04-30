from unittest.mock import patch

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound

import lms.views.api.canvas_studio as views


class TestAuthorize:
    def test_it(
        self, pyramid_request, canvas_studio_service, OAuthCallbackSchema, set_cookie
    ):
        result = views.authorize(pyramid_request)

        expected_state = OAuthCallbackSchema(pyramid_request).state_param()
        OAuthCallbackSchema.assert_called_with(pyramid_request)
        canvas_studio_service.authorization_url.assert_called_with(expected_state)
        assert result == {
            "redirect_url": canvas_studio_service.authorization_url.return_value,
            "link_text": "Canvas Studio login",
        }
        set_cookie.assert_called_once_with("canvas_studio_oauth_state", expected_state)

    def test_it_redirects_localhost(self, pyramid_request):
        pyramid_request.host_url = "http://localhost:8001"
        pyramid_request.url = "http://localhost:8001/api/canvas_studio/oauth/authorize"

        result = views.authorize(pyramid_request)

        assert result == Any.instance_of(HTTPFound).with_attrs(
            {
                "location": "https://hypothesis.local:48001/api/canvas_studio/oauth/authorize"
            }
        )

    @pytest.fixture
    def OAuthCallbackSchema(self, patch):
        OAuthCallbackSchema = patch("lms.views.api.canvas_studio.OAuthCallbackSchema")
        schema = OAuthCallbackSchema.return_value
        schema.state_param.return_value = "the-state"
        return OAuthCallbackSchema

    @pytest.fixture
    def set_cookie(self, pyramid_request):
        with patch.object(
            pyramid_request.response, "set_cookie", autospec=True
        ) as patched:
            yield patched


def test_oauth2_redirect(pyramid_request, canvas_studio_service):
    pyramid_request.parsed_params = {"code": "some_code"}
    views.oauth2_redirect(pyramid_request)
    canvas_studio_service.get_access_token.assert_called_once_with("some_code")


def test_oauth2_redirect_missing_state(pyramid_request):
    pyramid_request.params["code"] = "test_code"
    pyramid_request.cookies["canvas_studio_oauth_state"] = "test_state"

    redirect = views.oauth2_redirect_missing_state(pyramid_request)

    expected_location = "http://example.com/api/canvas_studio/oauth/callback?code=test_code&state=test_state"
    assert redirect == Any.instance_of(HTTPFound).with_attrs(
        {"location": expected_location}
    )


def test_list_media(canvas_studio_service, pyramid_request):
    result = views.list_media(pyramid_request)
    assert result == canvas_studio_service.list_media_library.return_value


def test_list_collection(canvas_studio_service, pyramid_request):
    pyramid_request.matchdict = {"collection_id": "42"}

    result = views.list_collection(pyramid_request)

    canvas_studio_service.list_collection.assert_called_with("42")
    assert result == canvas_studio_service.list_collection.return_value


@pytest.mark.usefixtures("canvas_studio_service", "assignment_service")
class TestViaURL:
    def test_it(self, canvas_studio_service, pyramid_request, via_video_url):
        response = views.via_url(pyramid_request)

        canvas_studio_service.get_canonical_video_url.assert_called_with("42")
        canvas_studio_service.get_video_download_url.assert_called_with("42")
        canvas_studio_service.get_transcript_url.assert_called_with("42")

        canonical_url = canvas_studio_service.get_canonical_video_url.return_value
        download_url = canvas_studio_service.get_video_download_url.return_value
        transcript_url = canvas_studio_service.get_transcript_url.return_value
        via_video_url.assert_called_with(
            pyramid_request, canonical_url, download_url, transcript_url
        )
        assert response["via_url"] == via_video_url.return_value

    def test_it_raises_if_transcript_not_available(
        self, canvas_studio_service, pyramid_request
    ):
        canvas_studio_service.get_transcript_url.return_value = None

        with pytest.raises(
            views.CanvasStudioLaunchError,
            match="This video does not have a published transcript",
        ) as exc_info:
            views.via_url(pyramid_request)

        assert exc_info.value.error_code == "canvas_studio_transcript_unavailable"

    def test_it_raises_if_document_url_not_valid(
        self, pyramid_request, assignment_service
    ):
        assignment_service.get_assignment.return_value.document_url = (
            "https://not-a-canvas-studio-url.com"
        )
        with pytest.raises(
            views.CanvasStudioLaunchError, match="Unable to get Canvas Studio media ID"
        ) as exc_info:
            views.via_url(pyramid_request)

        assert exc_info.value.error_code == "canvas_studio_media_not_found"

    def test_it_raises_if_download_not_available(
        self, canvas_studio_service, pyramid_request
    ):
        canvas_studio_service.get_video_download_url.return_value = None

        with pytest.raises(
            views.CanvasStudioLaunchError,
            match="Hypothesis was unable to fetch the video",
        ) as exc_info:
            views.via_url(pyramid_request)

        assert exc_info.value.error_code == "canvas_studio_download_unavailable"

    @pytest.fixture
    def via_video_url(self, patch):
        yield patch("lms.views.api.canvas_studio.via_video_url")

    @pytest.fixture
    def assignment_service(self, assignment_service):
        assignment_service.get_assignment.return_value.document_url = (
            "canvas-studio://media/42"
        )
        return assignment_service
