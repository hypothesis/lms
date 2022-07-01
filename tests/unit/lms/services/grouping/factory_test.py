from unittest.mock import sentinel

import pytest

from lms.services.grouping.factory import service_factory


@pytest.mark.usefixtures("application_instance_service", "with_plugins")
class TestFactory:
    def test_it(self, pyramid_request, application_instance_service, GroupingService):
        svc = service_factory(sentinel.context, pyramid_request)

        application_instance_service.get_current.assert_called_once_with()

        GroupingService.assert_called_once_with(
            db=pyramid_request.db,
            request=pyramid_request,
            application_instance=application_instance_service.get_current.return_value,
            plugin=pyramid_request.product.plugin.grouping_service,
        )

        assert svc == GroupingService.return_value

    @pytest.fixture
    def GroupingService(self, patch):
        return patch("lms.services.grouping.factory.GroupingService")
