from contextlib import ExitStack
from unittest.mock import patch

import pytest

from lms.product.blackboard import BlackboardProduct
from lms.product.canvas import CanvasProduct
from lms.product.factory import get_product_from_request
from lms.product.generic import GenericProduct
from lms.product.product import Product


class TestGetProductFromRequest:
    PRODUCTS = (GenericProduct, BlackboardProduct, CanvasProduct)
    PRODUCT_MAP = [
        # Products with a specific implementation
        ("BlackboardLearn", Product.Family.BLACKBOARD, BlackboardProduct),
        ("canvas", Product.Family.CANVAS, CanvasProduct),
        # Products with no specific implementation
        ("BlackbaudK12", Product.Family.BLACKBAUD, GenericProduct),
        ("desire2learn", Product.Family.D2L, GenericProduct),
        ("moodle", Product.Family.MOODLE, GenericProduct),
        ("schoology", Product.Family.SCHOOLOGY, GenericProduct),
        ("sakai", Product.Family.SAKAI, GenericProduct),
        # Non-matching products
        ("wut", Product.Family.UNKNOWN, GenericProduct),
        ("", Product.Family.UNKNOWN, GenericProduct),
        (None, Product.Family.UNKNOWN, GenericProduct),
    ]

    @pytest.mark.parametrize("value,family,class_", PRODUCT_MAP)
    def test_from_request_exact_match_lti(self, pyramid_request, value, family, class_):
        pyramid_request.lti_params["tool_consumer_info_product_family_code"] = value

        product = get_product_from_request(pyramid_request)

        class_.from_request.assert_called_once_with(pyramid_request)
        assert product == class_.from_request.return_value
        assert product.family == family

    @pytest.mark.parametrize("value,family,class_", PRODUCT_MAP)
    def test_from_request_api(self, pyramid_request, value, family, class_):
        pyramid_request.content_type = "application/json"
        pyramid_request.json = {"lms": {"product": value}}

        product = get_product_from_request(pyramid_request)

        class_.from_request.assert_called_once_with(pyramid_request)
        assert product == class_.from_request.return_value
        assert product.family == family

    def test_from_request_canvas_custom(self, pyramid_request):
        pyramid_request.lti_params = {"custom_canvas_course_id": "course_id"}

        product = get_product_from_request(pyramid_request)

        # Pylint doesn't know we patched this
        # pylint: disable=no-member
        CanvasProduct.from_request.assert_called_once_with(pyramid_request)
        assert product == CanvasProduct.from_request.return_value
        assert product.family == Product.Family.CANVAS

    @pytest.fixture(autouse=True)
    def with_mocked_from_request(self):
        with ExitStack() as stack:
            from_requests = [
                stack.enter_context(patch.object(product_class, "from_request"))
                for product_class in self.PRODUCTS
            ]

            yield from_requests
