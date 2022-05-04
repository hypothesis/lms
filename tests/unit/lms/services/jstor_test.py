from unittest.mock import sentinel

import pytest

from lms.models import ApplicationSettings
from lms.services.jstor import JSTORService, factory


class TestJSTORService:
    @pytest.mark.parametrize("enabled", (True, False, None))
    @pytest.mark.parametrize("site_code", ("code", None, ""))
    def test_enabled(self, enabled, site_code):
        svc = JSTORService(enabled=enabled, site_code=site_code)

        assert svc.enabled == bool(enabled and site_code)

    def test_via_url(self, pyramid_request, via_url):
        svc = JSTORService(enabled=True, site_code=sentinel.site_code)

        url = svc.via_url(pyramid_request, "jstor://doi")

        via_url.assert_called_once_with(
            pyramid_request,
            "jstor://doi",
            content_type="pdf",
            options={"via.jstor.site_code": sentinel.site_code},
        )

        assert url == via_url.return_value

    @pytest.fixture
    def via_url(self, patch):
        return patch("lms.services.jstor.via_url")


class TestFactory:
    def test_it(self, pyramid_request, application_instance_service, JSTORService):
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

        svc = factory(sentinel.context, pyramid_request)

        JSTORService.assert_called_once_with(
            enabled=sentinel.jstor_enabled, site_code=sentinel.jstor_site_code
        )
        assert svc == JSTORService.return_value

    @pytest.fixture(autouse=True)
    def JSTORService(self, patch):
        return patch("lms.services.jstor.JSTORService")
