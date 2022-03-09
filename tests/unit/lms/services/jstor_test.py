from unittest.mock import sentinel

import pytest

from lms.services.jstor import JSTORService, factory
from tests.conftest import TEST_SETTINGS


class TestUserService:
    @pytest.mark.parametrize(
        "settings,expected",
        [({}, False), ({"enabled": False}, False), ({"enabled": True}, True)],
    )
    def test_enabled(self, settings, expected):
        assert JSTORService(settings).enabled == expected

    def test_via_url(self, pyramid_request, via_url):
        url = JSTORService({}).via_url(pyramid_request, "jstor://doi")

        via_url.assert_called_once_with(
            pyramid_request,
            "jstor://doi",
            content_type="pdf",
            options={"jstor.ip": TEST_SETTINGS["jstor_ip"]},
        )

        assert url == via_url.return_value

    @pytest.fixture
    def via_url(self, patch):
        return patch("lms.services.jstor.via_url")


class TestFactory:
    def test_it(self, pyramid_request, application_instance_service, JSTORService):
        user_service = factory(sentinel.context, pyramid_request)

        JSTORService.assert_called_once_with(
            dict(application_instance_service.get_current.return_value.settings).get(
                "jstor", {}
            ),
        )
        assert user_service == JSTORService.return_value

    @pytest.fixture(autouse=True)
    def JSTORService(self, patch):
        return patch("lms.services.jstor.JSTORService")
