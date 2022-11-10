from contextlib import ExitStack
from unittest.mock import Mock, patch

import pytest

from lms.product.blackboard import Blackboard
from lms.product.canvas import Canvas
from lms.product.factory import get_product_from_request
from lms.product.product import Product
from lms.services.application_instance import ApplicationInstanceNotFound


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
    def test_from_request_exact_match_lti(
        self, pyramid_request, value, family, class_, application_instance
    ):
        pyramid_request.lti_params["tool_consumer_info_product_family_code"] = value

        product = get_product_from_request(pyramid_request)

        class_.from_request.assert_called_once_with(
            pyramid_request, application_instance.settings
        )
        assert product == class_.from_request.return_value
        assert product.family == family

    @pytest.mark.parametrize(
        "route_name,family",
        [
            ("canvas_api.endpoint", Product.Family.CANVAS),
            ("blackboard_api.endpoint", Product.Family.BLACKBOARD),
        ],
    )
    def test_from_request_route_name(self, pyramid_request, route_name, family):
        pyramid_request.matched_route.name = route_name
        assert get_product_from_request(pyramid_request).family == family

    @pytest.mark.parametrize("value,family,class_", PRODUCT_MAP)
    def test_from_request_api(
        self, pyramid_request, value, family, class_, application_instance
    ):
        pyramid_request.content_type = "application/json"
        pyramid_request.json = {"lms": {"product": value}}

        product = get_product_from_request(pyramid_request)

        class_.from_request.assert_called_once_with(
            pyramid_request, application_instance.settings
        )
        assert product == class_.from_request.return_value
        assert product.family == family

    def test_from_request_canvas_custom(self, pyramid_request, application_instance):
        pyramid_request.lti_params = {"custom_canvas_course_id": "course_id"}

        product = get_product_from_request(pyramid_request)

        # Pylint doesn't know we patched this
        # pylint: disable=no-member
        Canvas.from_request.assert_called_once_with(
            pyramid_request, application_instance.settings
        )
        assert product == Canvas.from_request.return_value
        assert product.family == Product.Family.CANVAS

    @pytest.mark.parametrize("value,family,class_", PRODUCT_MAP)
    def test_from_application_instance(
        self, pyramid_request, application_instance, value, family, class_
    ):
        application_instance.tool_consumer_info_product_family_code = value

        product = get_product_from_request(pyramid_request)

        class_.from_request.assert_called_once_with(
            pyramid_request, application_instance.settings
        )
        assert product == class_.from_request.return_value
        assert product.family == family

    def test_from_application_instance_when_missing(
        self, pyramid_request, application_instance_service
    ):
        application_instance_service.get_current.side_effect = (
            ApplicationInstanceNotFound()
        )

        product = get_product_from_request(pyramid_request)

        assert product.family == Product.Family.UNKNOWN

    @pytest.fixture(autouse=True)
    def with_mocked_from_request(self):
        with ExitStack() as stack:
            from_requests = [
                stack.enter_context(patch.object(product_class, "from_request"))
                for product_class in self.PRODUCTS
            ]

            yield from_requests

    @pytest.fixture()
    def pyramid_request(self, pyramid_request):
        pyramid_request.matched_route = Mock(spec_set=["name"])
        pyramid_request.matched_route.name = "some.route"
        return pyramid_request
