import pytest

from lms.models._hashed_id import hashed_id


class TestHashedId:
    @pytest.mark.parametrize(
        "parts,resulting_id",
        (
            (["a", 1, None], "f975d6bab6cf2c8046233dacc9332b2b0b2b2810"),
            (["b", 1, None], "977b5d9c262d94c91a784635e72e63583e6d0024"),
            (
                [ValueError(), 1.2234, "thing"],
                "697ea95083b8e46a97eb3d30bf0320e7a7485929",
            ),
        ),
    )
    def test_golden_master(self, parts, resulting_id):
        # Some canned responses that prove the algorithm hasn't changed and
        # that it doesn't fall over
        assert hashed_id(*parts) == resulting_id
