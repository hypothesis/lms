from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound

from lms.resources._js_config import JSConfig
from lms.resources.dashboard import DashboardResource
from lms.views.dashboard import DashboardViews

pytestmark = pytest.mark.usefixtures("h_api", "assignment_service")


class TestDashboardViews:
    def test_assignment_redirect_from_launch(self, views, pyramid_request):
        pyramid_request.matchdict["id_"] = sentinel.id

        response = views.assignment_redirect_from_launch()

        assert response == Any.instance_of(HTTPFound).with_attrs(
            {
                "location": "http://example.com/dashboard/assignment/sentinel.id",
            }
        )

    def test_assignment_show(self, views, pyramid_request, assignment_service):
        context = DashboardResource(pyramid_request)
        context.js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        pyramid_request.context = context
        pyramid_request.matchdict["id_"] = sentinel.id

        views.assignment_show()

        assignment_service.get_by_id.assert_called_once_with(sentinel.id)
        pyramid_request.context.js_config.enable_dashboard_mode.assert_called_once_with(
            assignment_service.get_by_id.return_value
        )

    @pytest.fixture
    def views(self, pyramid_request):
        return DashboardViews(pyramid_request)
