from unittest import mock
from unittest.mock import sentinel

import pytest

from lms.models.region import Region, Regions


class TestRegion:
    @pytest.mark.parametrize(
        "code,name", [("us", "Worldwide (U.S.)"), ("ca", "Canada")]
    )
    def test_it(self, code, name):
        region = Region(code=code, authority=sentinel.authority)

        assert region.code == code
        assert region.authority == sentinel.authority
        assert region.name == name

    def test_it_crashes_if_the_code_is_unknown(self):
        with pytest.raises(KeyError):
            Region(code="unknown_code", authority=sentinel.authority_)


class TestRegions:
    def test_get_region(self, current_region):
        current_region.return_value = Region(code="us", authority=sentinel.authority)

        assert Regions.get_region() == current_region.return_value

    def test_get_region_with_no_region(self, current_region):
        current_region.return_value = None

        with pytest.raises(ValueError):
            Regions.get_region()

    @pytest.mark.parametrize("bad_code", (None, "UNRECOGNIZED"))
    def test_set_region_raises_for_bad_codes(self, bad_code):
        with pytest.raises(KeyError):
            Regions.set_region(sentinel.authority, bad_code)

    @pytest.fixture
    def current_region(self):
        with mock.patch.object(Regions, "_current_region") as _current_region:
            _current_region.__get__ = mock.Mock(return_value=None)
            yield _current_region.__get__
