from unittest.mock import create_autospec

import pytest
from pyramid.config import Configurator

from lms.models.product import Product, includeme

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


class TestProduct:
    @pytest.mark.parametrize("value,expected", PRODUCT_NAMES)
    def test_from_request_exact_match_lti(self, value, expected, pyramid_request):
        pyramid_request.lti_params["tool_consumer_info_product_family_code"] = value

        assert Product.from_request(pyramid_request).family == expected

    @pytest.mark.parametrize("value,expected", PRODUCT_NAMES)
    def test_from_request_api(self, value, expected, pyramid_request):
        pyramid_request.content_type = "application/json"
        pyramid_request.json = {"lms": {"product": value}}

        assert Product.from_request(pyramid_request).family == expected

    def test_from_request_canvas_custom(self, pyramid_request):
        pyramid_request.lti_params = {"custom_canvas_course_id": "course_id"}

        assert Product.from_request(pyramid_request).family == Product.Family.CANVAS


class TestIncludeMe:
    def test_it_sets_request_method(self, configurator):
        includeme(configurator)

        configurator.add_request_method.assert_called_once_with(
            Product.from_request, name="product", property=True, reify=True
        )

    @pytest.fixture()
    def configurator(self):
        return create_autospec(Configurator, spec_set=True, instance=True)
