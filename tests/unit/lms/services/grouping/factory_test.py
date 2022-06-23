from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.product import Product
from lms.services.grouping.factory import service_factory


@pytest.mark.usefixtures("application_instance_service")
class TestFactory:
    def test_it(
        self,
        pyramid_request,
        application_instance_service,
        GroupingService,
        GroupingServicePlugin,
    ):
        svc = service_factory(sentinel.context, pyramid_request)

        application_instance_service.get_current.assert_called_once_with()

        GroupingService.assert_called_once_with(
            db=pyramid_request.db,
            application_instance=application_instance_service.get_current.return_value,
            plugin=GroupingServicePlugin.return_value,
        )

        assert svc == GroupingService.return_value

    def test_it_in_canvas(
        self, canvas_api_client, CanvasGroupingPlugin, pyramid_request, GroupingService
    ):
        pyramid_request.product.family = Product.Family.CANVAS

        service_factory(sentinel.context, pyramid_request)

        CanvasGroupingPlugin.assert_called_once_with(canvas_api_client)
        GroupingService.assert_called_once_with(
            db=Any(),
            application_instance=Any(),
            plugin=CanvasGroupingPlugin.return_value,
        )

    def test_it_in_blackboard(
        self,
        blackboard_api_client,
        BlackboardGroupingPlugin,
        pyramid_request,
        GroupingService,
    ):
        pyramid_request.product.family = Product.Family.BLACKBOARD

        service_factory(sentinel.context, pyramid_request)

        BlackboardGroupingPlugin.assert_called_once_with(blackboard_api_client)
        GroupingService.assert_called_once_with(
            db=Any(),
            application_instance=Any(),
            plugin=BlackboardGroupingPlugin.return_value,
        )

    @pytest.fixture
    def GroupingService(self, patch):
        return patch("lms.services.grouping.factory.GroupingService")

    @pytest.fixture
    def BlackboardGroupingPlugin(self, patch):
        return patch("lms.services.grouping.factory.BlackboardGroupingPlugin")

    @pytest.fixture
    def CanvasGroupingPlugin(self, patch):
        return patch("lms.services.grouping.factory.CanvasGroupingPlugin")

    @pytest.fixture
    def GroupingServicePlugin(self, patch):
        return patch("lms.services.grouping.factory.GroupingServicePlugin")
