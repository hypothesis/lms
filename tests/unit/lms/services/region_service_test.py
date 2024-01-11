from unittest.mock import sentinel

import pytest

from lms.models import Region
from lms.services.region import RegionService, factory


class TestRegionService:
    def test_get(self, svc):
        assert svc.get() == Region(code="us", authority=sentinel.authority)

    @pytest.fixture
    def svc(self):
        return RegionService(region_code="us", authority=sentinel.authority)


class TestFactory:
    def test_it(self, pyramid_request, RegionService):
        region_service = factory(sentinel.context, pyramid_request)

        RegionService.assert_called_once_with(
            region_code="us", authority="lms.hypothes.is"
        )
        assert region_service == RegionService.return_value

    @pytest.fixture(autouse=True)
    def RegionService(self, patch):
        return patch("lms.services.region.RegionService")
