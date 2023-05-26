from unittest.mock import sentinel

import pytest

from lms.services.youtube import VideoNotFound, YoutubeService, factory
from tests import factories


class TestYoutubeService:
    @pytest.mark.parametrize(
        "enabled,api_key,expected_enabled",
        (
            (True, "api_key", True),
            (True, "", False),
            (False, "api_key", False),
            (False, "", False),
            (None, "api_key", False),
            (None, "", False),
        ),
    )
    def test_enabled(self, enabled, api_key, expected_enabled, http_service):
        svc = YoutubeService(enabled=enabled, api_key=api_key, http=http_service)

        assert svc.enabled == expected_enabled

    def test_video_info_raises_for_invalid_video(self, svc, http_service):
        response = factories.requests.Response(json_data={"items": []})
        http_service.get.return_value = response

        with pytest.raises(VideoNotFound):
            svc.video_info(video_id="invalid_video_id")

    def test_video_info_parses_json_response(self, svc, http_service):
        response = factories.requests.Response(
            json_data={
                "items": [
                    {
                        "snippet": {
                            "title": "Some video",
                            "channelTitle": "Hypothesis",
                            "thumbnails": {
                                "medium": {
                                    "url": "https://i.ytimg.com/vi/EU6TDnV5osM/mqdefault.jpg"
                                }
                            },
                        },
                        "contentDetails": {"duration": "P2M10S"},
                    }
                ]
            }
        )
        http_service.get.return_value = response

        result = svc.video_info(video_id="invalid_video_id")
        assert result == {
            "title": "Some video",
            "channel": "Hypothesis",
            "image": "https://i.ytimg.com/vi/EU6TDnV5osM/mqdefault.jpg",
            "duration": "P2M10S",
        }

    @pytest.fixture
    def svc(self, http_service):
        return YoutubeService(enabled=True, api_key="api_key", http=http_service)


class TestServiceFactory:
    @pytest.mark.usefixtures("application_instance_service")
    @pytest.mark.usefixtures("http_service")
    def test_it(
        self, pyramid_request, application_instance, YoutubeService, http_service
    ):
        application_instance.settings.set("youtube", "enabled", sentinel.enabled)

        app_settings = pyramid_request.registry.settings
        app_settings["youtube_api_key"] = "api_key"

        svc = factory(sentinel.context, pyramid_request)

        YoutubeService.assert_called_once_with(
            enabled=sentinel.enabled, api_key="api_key", http=http_service
        )
        assert svc == YoutubeService.return_value

    @pytest.fixture
    def YoutubeService(self, patch):
        return patch("lms.services.youtube.YoutubeService")
