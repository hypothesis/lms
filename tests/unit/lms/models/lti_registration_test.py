import pytest

from lms.models.family import Family
from tests import factories


class TestLTIRegistration:
    @pytest.mark.parametrize(
        "issuer,family",
        [
            ("SOMEURL", Family.UNKNOWN),
            ("https://canvas.instructure.com", Family.CANVAS),
        ],
    )
    def test_product_family(self, issuer, family):
        assert factories.LTIRegistration(issuer=issuer).product_family == family
