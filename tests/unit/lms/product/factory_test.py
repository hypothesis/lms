import pytest

from lms.product.blackboard import Blackboard
from lms.product.canvas import Canvas
from lms.product.factory import get_product_from_request
from lms.product.product import Product


@pytest.mark.usefixtures("application_instance_service")
class TestGetProductFromRequest:
    PRODUCTS = (Product, Blackboard, Canvas)
    PRODUCT_MAP = [
        # Products with a specific implementation
        ("BlackboardLearn", Product.Family.BLACKBOARD, Blackboard),
        ("canvas", Product.Family.CANVAS, Canvas),
        # Products with no specific implementation
        ("BlackbaudK12", Product.Family.BLACKBAUD, Product),
        ("desire2learn", Product.Family.D2L, Product),
        ("moodle", Product.Family.MOODLE, Product),
        ("schoology", Product.Family.SCHOOLOGY, Product),
        ("sakai", Product.Family.SAKAI, Product),
        # Non-matching products
        ("wut", Product.Family.UNKNOWN, Product),
        ("", Product.Family.UNKNOWN, Product),
        (None, Product.Family.UNKNOWN, Product),
    ]

    @pytest.mark.parametrize("value,family,class_", PRODUCT_MAP)
    def test_from_launch(self, pyramid_request, value, family, class_):
        pyramid_request.lti_user.lti.product_family = value

        product = get_product_from_request(pyramid_request)

        assert isinstance(product, class_)
        assert product.family == family

    def test_from_launch_with_no_lti_user(self, pyramid_request):
        pyramid_request.lti_user = None

        product = get_product_from_request(pyramid_request)

        assert product.family == Product.Family.UNKNOWN
