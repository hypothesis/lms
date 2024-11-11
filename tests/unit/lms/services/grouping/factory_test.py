from unittest.mock import sentinel

import pytest

from lms.services.grouping.factory import service_factory


@pytest.mark.usefixtures("application_instance_service", "with_plugins")
class TestFactory:
    def test_it(
        self, pyramid_request, application_instance, GroupingService, segment_service
    ):
        svc = service_factory(sentinel.context, pyramid_request)

        GroupingService.assert_called_once_with(
            db=pyramid_request.db,
            application_instance=application_instance,
            plugin=pyramid_request.product.plugin.grouping,
            segment_service=segment_service,
        )

        assert svc == GroupingService.return_value

    @pytest.fixture
    def GroupingService(self, patch):
        return patch("lms.services.grouping.factory.GroupingService")
