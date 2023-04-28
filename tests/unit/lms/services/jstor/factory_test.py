from unittest.mock import sentinel

import pytest

from lms.services.jstor.factory import service_factory


class TestServiceFactory:
    @pytest.mark.parametrize("user_agent", ("Example UA", None))
    def test_it(
        self, pyramid_request, application_instance_service, JSTORService, user_agent
    ):
        ai_settings = pyramid_request.lti_user.application_instance.settings
        ai_settings.set("jstor", "enabled", sentinel.jstor_enabled)
        ai_settings.set("jstor", "site_code", sentinel.jstor_site_code)

        reg_settings = pyramid_request.registry.settings
        reg_settings["jstor_api_url"] = sentinel.jstor_api_url
        reg_settings["jstor_api_secret"] = sentinel.jstor_api_secret

        if user_agent:
            pyramid_request.headers["User-Agent"] = user_agent

        svc = service_factory(sentinel.context, pyramid_request)

        JSTORService.assert_called_once_with(
            api_url=sentinel.jstor_api_url,
            secret=sentinel.jstor_api_secret,
            enabled=sentinel.jstor_enabled,
            site_code=sentinel.jstor_site_code,
            headers={
                "Tracking-User-ID": pyramid_request.lti_user.h_user.username,
                "Tracking-User-Agent": user_agent,
            },
        )
        assert svc == JSTORService.return_value

    @pytest.fixture
    def JSTORService(self, patch):
        return patch("lms.services.jstor.factory.JSTORService")
