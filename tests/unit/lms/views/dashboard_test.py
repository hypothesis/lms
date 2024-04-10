from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound

from lms.resources._js_config import JSConfig
from lms.resources.dashboard import DashboardResource
from lms.views.dashboard import DashboardViews
from tests import factories

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

    def test_api_assignment_stats(
        self, views, pyramid_request, assignment_service, h_api
    ):
        pyramid_request.matchdict["id_"] = sentinel.id
        assignment = factories.Assignment()
        assignment_service.get_by_id.return_value = assignment
        stats = [
            {
                "display_name": sentinel.display_name,
                "annotations": sentinel.annotations,
                "replies": sentinel.replies,
                "last_activity": sentinel.last_activity,
                "extra_data": sentinel.extra_data,
            }
        ]

        h_api.get_assignment_stats.return_value = stats

        response = views.api_assignment_stats()

        assignment_service.get_by_id.assert_called_once_with(sentinel.id)
        h_api.get_assignment_stats.assert_called_once_with(
            [g.authority_provided_id for g in assignment.groupings],
            assignment.resource_link_id,
        )
        assert response == [
            {
                "display_name": s["display_name"],
                "annotations": s["annotations"],
                "replies": s["replies"],
                "last_activity": s["last_activity"],
            }
            for s in stats
        ]

    @pytest.fixture
    def views(self, pyramid_request):
        return DashboardViews(pyramid_request)
