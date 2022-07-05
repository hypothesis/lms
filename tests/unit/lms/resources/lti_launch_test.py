from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.product import Product
from lms.resources import LTILaunchResource


@pytest.mark.usefixtures("application_instance_service", "assignment_service")
class TestLTILaunchResource:
    def test_application_instance(self, ctx, application_instance_service):
        application_instance = ctx.application_instance

        application_instance_service.get_current.assert_called_once_with()
        assert (
            application_instance
            == application_instance_service.get_current.return_value
        )

    def test_course(self, ctx, pyramid_request, course_service):
        course = ctx.course

        course_service.upsert_course.assert_called_once_with(
            context_id=pyramid_request.parsed_params["context_id"],
            name=pyramid_request.parsed_params["context_title"],
            extra={},
        )
        assert course == course_service.upsert_course.return_value

    def test_course_with_canvas(self, ctx, pyramid_request, course_service):
        pyramid_request.product.family = Product.Family.CANVAS
        pyramid_request.parsed_params["custom_canvas_course_id"] = "ID"

        assert ctx.course

        course_service.upsert_course.assert_called_once_with(
            context_id=Any(),
            name=Any(),
            extra={"canvas": {"custom_canvas_course_id": "ID"}},
        )

    def test_grouping_type(self, ctx, grouping_service):
        grouping_type = ctx.grouping_type

        grouping_service.get_grouping_type.assert_called_once_with()
        assert grouping_type == grouping_service.get_grouping_type.return_value

    @pytest.mark.parametrize(
        "product,expected",
        [
            (Product.Family.CANVAS, True),
            (Product.Family.BLACKBOARD, False),
            (Product.Family.UNKNOWN, False),
        ],
    )
    def test_is_canvas(self, ctx, pyramid_request, product, expected):
        pyramid_request.product.family = product

        assert ctx.is_canvas == expected

    def test_js_config(self, ctx, pyramid_request, JSConfig):
        js_config = ctx.js_config

        JSConfig.assert_called_once_with(ctx, pyramid_request)
        assert js_config == JSConfig.return_value

    @pytest.fixture
    def ctx(self, pyramid_request):
        return LTILaunchResource(pyramid_request)

    @pytest.fixture
    def JSConfig(self, patch):
        return patch("lms.resources.lti_launch.JSConfig")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "context_id": sentinel.context_id,
            "context_title": sentinel.context_title,
        }
        return pyramid_request
