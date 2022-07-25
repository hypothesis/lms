from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.services.vitalsource.factory import service_factory


class TestServiceFactory:
    @pytest.mark.parametrize(
        "enabled,expected", ((sentinel.enabled, sentinel.enabled), (None, False))
    )
    def test_it(
        self,
        pyramid_request,
        VitalSourceService,
        VitalSourceClient,
        application_instance_service,
        enabled,
        expected,
    ):
        # This fixture is a bit odd and returns a real application instance
        ai = application_instance_service.get_current()
        if enabled:
            ai.settings.set("vitalsource", "enabled", enabled)

        svc = service_factory(sentinel.context, pyramid_request)

        VitalSourceClient.assert_called_once_with(api_key="test_vs_api_key")
        VitalSourceService.assert_called_once_with(
            client=VitalSourceClient.return_value, enabled=expected
        )
        assert svc == VitalSourceService.return_value

    @pytest.mark.usefixtures("application_instance_service")
    def test_it_when_no_api_key(self, pyramid_request, VitalSourceService):
        pyramid_request.registry.settings["vitalsource_api_key"] = None

        svc = service_factory(sentinel.context, pyramid_request)

        VitalSourceService.assert_called_once_with(
            client=None, enabled=Any(), user_lti_param=Any()
        )
        assert svc == VitalSourceService.return_value

    @pytest.fixture
    def VitalSourceService(self, patch):
        return patch("lms.services.vitalsource.factory.VitalSourceService")

    @pytest.fixture
    def VitalSourceClient(self, patch):
        return patch("lms.services.vitalsource.factory.VitalSourceClient")
