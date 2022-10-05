from unittest import mock
from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any
from pyramid.config import Configurator

from lms.models.region import Regions, includeme


class TestRegions:
    @pytest.mark.parametrize("code,region", (("us", Regions.US), ("ca", Regions.CA)))
    def test_from_code(self, code, region):
        assert Regions.from_code(code) == region

    @pytest.mark.parametrize("bad_code", (None, "UNRECOGNIZED"))
    def test_from_code_raises_ValueError_for_bad_code(self, bad_code):
        with pytest.raises(ValueError):
            Regions.from_code(bad_code)

    def test_get_region(self, current_region):
        current_region.return_value = Regions.CA

        assert Regions.get_region() == Regions.CA

    def test_get_region_with_no_region(self, current_region):
        current_region.return_value = None

        with pytest.raises(ValueError):
            Regions.get_region()

    @pytest.mark.parametrize("bad_authority", (None, "UNRECOGNIZED"))
    def test_from_request_raises_ValueError_for_bad_authorities(
        self, pyramid_request, bad_authority
    ):
        pyramid_request.registry.settings["h_authority"] = bad_authority

        with pytest.raises(ValueError):
            Regions.set_region(pyramid_request)

    @pytest.fixture
    def current_region(self):
        with mock.patch.object(Regions, "_current_region") as _current_region:
            _current_region.__get__ = mock.Mock(return_value=None)
            yield _current_region.__get__


class TestIncludeMe:
    def test_it(self, configurator, Regions):
        includeme(configurator)

        any_callable = Any.callable()

        configurator.add_request_method.assert_called_once_with(
            any_callable, name="region", property=True, reify=True
        )

        # You can use h-matchers as spies to capture what they last matched
        response = any_callable.last_matched()(sentinel.request)
        Regions.get_region.assert_called_once_with()
        assert response == Regions.get_region.return_value

    @pytest.fixture
    def configurator(self):
        return create_autospec(Configurator, spec_set=True, instance=True)

    @pytest.fixture
    def Regions(self, patch):
        return patch("lms.models.region.Regions")
