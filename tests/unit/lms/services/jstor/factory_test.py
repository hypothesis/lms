from unittest.mock import sentinel

import pytest

from lms.models import ApplicationSettings
from lms.services.jstor.factory import service_factory


class TestServiceFactory:
    def test_it(
        self, pyramid_request, application_instance_service, http_service, JSTORService
    ):
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
        pyramid_request.registry.settings.update(
            {
                "jstor_api_url": sentinel.jstor_api_url,
                "jstor_api_secret": sentinel.jstor_api_secret,
            }
        )

        svc = service_factory(sentinel.context, pyramid_request)

        JSTORService.assert_called_once_with(
            api_url=sentinel.jstor_api_url,
            secret=sentinel.jstor_api_secret,
            enabled=sentinel.jstor_enabled,
            site_code=sentinel.jstor_site_code,
            http_service=http_service,
        )
        assert svc == JSTORService.return_value

    @pytest.fixture
    def JSTORService(self, patch):
        return patch("lms.services.jstor.factory.JSTORService")
