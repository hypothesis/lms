import pytest

from lms.views.api.youtube import YouTubeAPIViews


@pytest.mark.usefixtures("youtube_service")
class TestYouTubeAPIViews:
    def test_video_info(self, views, youtube_service, pyramid_request):
        pyramid_request.matchdict["video_id"] = "test-video-id"

        video_info = views.video_info()

        youtube_service.video_info("test-video-id")
        assert video_info == youtube_service.video_info.return_value

    @pytest.fixture
    def views(self, pyramid_request):
        return YouTubeAPIViews(pyramid_request)
