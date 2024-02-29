import pytest

from lms.product.family import Family
from lms.product.product import Product


class TestFromLaunch:
    PRODUCT_MAP = [
        ("BlackboardLearn", Product.Family.BLACKBOARD),
        ("canvas", Product.Family.CANVAS),
        ("BlackbaudK12", Product.Family.BLACKBAUD),
        ("desire2learn", Product.Family.D2L),
        ("moodle", Product.Family.MOODLE),
        ("schoology", Product.Family.SCHOOLOGY),
        ("sakai", Product.Family.SAKAI),
        ("wut", Product.Family.UNKNOWN),
        ("", Product.Family.UNKNOWN),
        (None, Product.Family.UNKNOWN),
    ]

    @pytest.mark.parametrize("value,family", PRODUCT_MAP)
    def test_from_lti_parameter(self, value, family):
        assert (
            Family.from_launch({"tool_consumer_info_product_family_code": value})
            == family
        )

    def test_from_request_canvas_custom(self):
        assert (
            Family.from_launch({"custom_canvas_course_id": "course_id"})
            == Family.CANVAS
        )

    def test_fallback(self):
        assert Family.from_launch({}) == Family.UNKNOWN
