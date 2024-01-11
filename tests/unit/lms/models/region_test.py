from unittest.mock import sentinel

import pytest

from lms.models.region import Region


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
