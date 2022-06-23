import pytest

from lms.product.factory import get_product_from_request
from lms.product.product import Product


class TestGetProductFromRequest:
    PRODUCT_NAMES = [
        ("BlackbaudK12", Product.Family.BLACKBAUD),
        ("BlackboardLearn", Product.Family.BLACKBOARD),
        ("canvas", Product.Family.CANVAS),
        ("desire2learn", Product.Family.D2L),
        ("moodle", Product.Family.MOODLE),
        ("schoology", Product.Family.SCHOOLOGY),
        ("sakai", Product.Family.SAKAI),
        ("wut", Product.Family.UNKNOWN),
        ("", Product.Family.UNKNOWN),
        (None, Product.Family.UNKNOWN),
    ]

    @pytest.mark.parametrize("value,expected", PRODUCT_NAMES)
    def test_from_request_exact_match_lti(self, value, expected, pyramid_request):
        pyramid_request.lti_params["tool_consumer_info_product_family_code"] = value

        product = get_product_from_request(pyramid_request)

        assert isinstance(product, Product)
        assert product.family == expected

    @pytest.mark.parametrize("value,expected", PRODUCT_NAMES)
    def test_from_request_api(self, value, expected, pyramid_request):
        pyramid_request.content_type = "application/json"
        pyramid_request.json = {"lms": {"product": value}}

        product = get_product_from_request(pyramid_request)

        assert isinstance(product, Product)
        assert product.family == expected

    def test_from_request_canvas_custom(self, pyramid_request):
        pyramid_request.lti_params = {"custom_canvas_course_id": "course_id"}

        product = get_product_from_request(pyramid_request)

        assert isinstance(product, Product)
        assert product.family == Product.Family.CANVAS
