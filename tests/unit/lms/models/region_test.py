import pytest

from lms.models.region import Regions


class TestRegions:
    @pytest.mark.parametrize(
        "authority,region",
        (("lms.hypothes.is", Regions.US), ("lms.ca.hypothes.is", Regions.CA)),
    )
    def test_from_request(self, pyramid_request, authority, region):
        pyramid_request.registry.settings["h_authority"] = authority

        assert Regions.from_authority(pyramid_request) == region

    @pytest.mark.parametrize("bad_authority", (None, "UNRECOGNIZED"))
    def test_from_request_raises_ValueError_for_bad_authorities(
        self, pyramid_request, bad_authority
    ):
        pyramid_request.registry.settings["h_authority"] = bad_authority

        with pytest.raises(ValueError):
            Regions.from_authority(pyramid_request)
