from unittest import mock
from unittest.mock import sentinel

import pytest

from lms.models.region import Region, Regions


class TestRegions:
    @pytest.mark.parametrize(
        "code,region",
        (
            (
                "us",
                Region(
                    code="us", name="Worldwide (U.S.)", authority=sentinel.authority
                ),
            ),
            ("ca", Region(code="ca", name="Canada", authority=sentinel.authority)),
        ),
    )
    def test_from_code(self, code, region):
        assert Regions.from_code(sentinel.authority, code) == region

    @pytest.mark.parametrize("bad_code", (None, "UNRECOGNIZED"))
    def test_from_code_raises_ValueError_for_bad_code(self, bad_code):
        with pytest.raises(ValueError):
            Regions.from_code(sentinel.authority, bad_code)

    def test_get_region(self, current_region):
        current_region.return_value = Region(
            code=sentinel.code, name=sentinel.name, authority=sentinel.authority
        )

        assert Regions.get_region() == current_region.return_value

    def test_get_region_with_no_region(self, current_region):
        current_region.return_value = None

        with pytest.raises(ValueError):
            Regions.get_region()

    @pytest.mark.parametrize("bad_code", (None, "UNRECOGNIZED"))
    def test_set_region_raises_ValueError_for_bad_codes(self, bad_code):
        with pytest.raises(ValueError):
            Regions.set_region(sentinel.authority, bad_code)

    @pytest.fixture
    def current_region(self):
        with mock.patch.object(Regions, "_current_region") as _current_region:
            _current_region.__get__ = mock.Mock(return_value=None)
            yield _current_region.__get__
