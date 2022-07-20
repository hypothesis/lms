from unittest.mock import sentinel

import pytest

from lms.services.vitalsource.factory import service_factory


class TestServiceFactory:
    def test_it(self, pyramid_request, VitalSourceService, VitalSourceClient):
        svc = service_factory(sentinel.context, pyramid_request)

        VitalSourceClient.assert_called_once_with(api_key="test_vs_api_key")
        VitalSourceService.assert_called_once_with(VitalSourceClient.return_value)
        assert svc == VitalSourceService.return_value

    @pytest.fixture
    def VitalSourceService(self, patch):
        return patch("lms.services.vitalsource.factory.VitalSourceService")

    @pytest.fixture
    def VitalSourceClient(self, patch):
        return patch("lms.services.vitalsource.factory.VitalSourceClient")
