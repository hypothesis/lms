from unittest.mock import sentinel

import pytest

from lms.services.youtube import YoutubeService, factory


class TestYoutubeService:
    @pytest.mark.parametrize("enabled", (True, False, None))
    def test_enabled(self, enabled):
        svc = YoutubeService(enabled=enabled)

        assert svc.enabled == enabled


class TestServiceFactory:
    @pytest.mark.usefixtures("application_instance_service")
    def test_it(self, pyramid_request, application_instance, YoutubeService):
        application_instance.settings.set("youtube", "enabled", sentinel.enabled)

        svc = factory(sentinel.context, pyramid_request)

        YoutubeService.assert_called_once_with(enabled=sentinel.enabled)
        assert svc == YoutubeService.return_value

    @pytest.fixture
    def YoutubeService(self, patch):
        return patch("lms.services.youtube.YoutubeService")
