from unittest.mock import create_autospec

import pytest
from pyramid.config import Configurator

from lms.models.region import Regions, includeme


class TestRegions:
    @pytest.mark.parametrize(
        "authority,region",
        (("lms.hypothes.is", Regions.US), ("lms.ca.hypothes.is", Regions.CA)),
    )
    def test_from_request(self, pyramid_request, authority, region):
        pyramid_request.registry.settings["h_authority"] = authority

        assert Regions.from_request(pyramid_request) == region

    @pytest.mark.parametrize("bad_authority", (None, "UNRECOGNIZED"))
    def test_from_request_raises_ValueError_for_bad_authorities(
        self, pyramid_request, bad_authority
    ):
        pyramid_request.registry.settings["h_authority"] = bad_authority

        with pytest.raises(ValueError):
            Regions.from_request(pyramid_request)


class TestIncludeMe:
    def test_it(self, configurator):
        includeme(configurator)

        configurator.add_request_method.assert_called_once_with(
            Regions.from_request, name="region", property=True, reify=True
        )

    @pytest.fixture()
    def configurator(self):
        return create_autospec(Configurator, spec_set=True, instance=True)
