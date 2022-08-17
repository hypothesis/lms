from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.services.vitalsource.factory import service_factory


@pytest.mark.usefixtures("application_instance_service")
class TestServiceFactory:
    @pytest.mark.parametrize(
        "enabled,expected", ((sentinel.enabled, sentinel.enabled), (None, False))
    )
    @pytest.mark.parametrize("customer_api_key", (sentinel.customer_api_key, None))
    def test_it(
        self,
        pyramid_request,
        VitalSourceService,
        VitalSourceClient,
        application_instance_service,
        enabled,
        expected,
        customer_api_key,
    ):
        pyramid_request.registry.settings["vitalsource_api_key"] = None
        # This fixture is a bit odd and returns a real application instance
        ai = application_instance_service.get_current()
        ai.settings.set("vitalsource", "user_lti_param", sentinel.user_lti_param)
        ai.settings.set("vitalsource", "api_key", customer_api_key)
        if enabled:
            ai.settings.set("vitalsource", "enabled", enabled)

        svc = service_factory(sentinel.context, pyramid_request)

        if customer_api_key:
            VitalSourceClient.assert_called_once_with(customer_api_key)
        else:
            VitalSourceClient.assert_not_called()

        VitalSourceService.assert_called_once_with(
            enabled=expected,
            global_client=None,
            customer_client=VitalSourceClient.return_value
            if customer_api_key
            else None,
            user_lti_param=sentinel.user_lti_param,
        )
        assert svc == VitalSourceService.return_value

    @pytest.mark.parametrize("global_api_key", (sentinel.global_api_key, None))
    def test_it_with_a_global_key(
        self, pyramid_request, VitalSourceService, global_api_key, VitalSourceClient
    ):
        pyramid_request.registry.settings["vitalsource_api_key"] = global_api_key

        service_factory(sentinel.context, pyramid_request)

        if global_api_key:
            VitalSourceClient.assert_called_once_with(global_api_key)
        else:
            VitalSourceClient.assert_not_called()

        VitalSourceService.assert_called_once_with(
            enabled=Any(),
            global_client=VitalSourceClient.return_value if global_api_key else None,
            customer_client=Any(),
            user_lti_param=Any(),
        )

    @pytest.fixture
    def VitalSourceService(self, patch):
        return patch("lms.services.vitalsource.factory.VitalSourceService")

    @pytest.fixture
    def VitalSourceClient(self, patch):
        return patch("lms.services.vitalsource.factory.VitalSourceClient")
