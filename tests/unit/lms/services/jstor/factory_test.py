from unittest.mock import sentinel

import pytest

from lms.models import ApplicationSettings
from lms.services.jstor.factory import service_factory


class TestServiceFactory:
    def test_it(self, pyramid_request, http_service, JSTORService):
        svc = service_factory(sentinel.context, pyramid_request)

        JSTORService.assert_called_once_with(
            api_url=sentinel.jstor_api_url,
            secret=sentinel.jstor_api_secret,
            enabled=sentinel.jstor_enabled,
            site_code=sentinel.jstor_site_code,
            http_service=http_service,
            tracking_user_agent="Chrome 100",
            tracking_user_id=pyramid_request.lti_user.h_user.username,
        )
        assert svc == JSTORService.return_value

    def test_it_omits_tracking_info_if_not_available(
        self, pyramid_request, http_service, JSTORService
    ):
        del pyramid_request.headers["User-Agent"]
        pyramid_request.lti_user = None

        service_factory(sentinel.context, pyramid_request)

        JSTORService.assert_called_once_with(
            api_url=sentinel.jstor_api_url,
            secret=sentinel.jstor_api_secret,
            enabled=sentinel.jstor_enabled,
            site_code=sentinel.jstor_site_code,
            http_service=http_service,
            tracking_user_agent=None,
            tracking_user_id=None,
        )

    @pytest.fixture
    def JSTORService(self, patch):
        return patch("lms.services.jstor.factory.JSTORService")

    @pytest.fixture(autouse=True)
    def application_instance_service(self, application_instance_service):
        application_instance_service.get_current.return_value.settings = (
            ApplicationSettings(
                {
                    "jstor": {
                        "enabled": sentinel.jstor_enabled,
                        "site_code": sentinel.jstor_site_code,
                    }
                }
            )
        )
        return application_instance_service

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config):
        pyramid_config.registry.settings.update(
            {
                "jstor_api_url": sentinel.jstor_api_url,
                "jstor_api_secret": sentinel.jstor_api_secret,
            }
        )
        return pyramid_config

    @pytest.fixture(autouse=True)
    def pyramid_request(self, pyramid_request):
        pyramid_request.headers["User-Agent"] = "Chrome 100"
        return pyramid_request
