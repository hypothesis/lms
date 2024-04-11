from unittest.mock import create_autospec, sentinel

import pytest
from freezegun import freeze_time
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPUnauthorized

from lms.resources._js_config import JSConfig
from lms.resources.dashboard import DashboardResource
from lms.views.dashboard import DashboardViews
from tests import factories

pytestmark = pytest.mark.usefixtures("h_api", "assignment_service")


class TestDashboardViews:
    @freeze_time("2024-04-01 12:00:00")
    def test_assignment_redirect_from_launch(
        self, views, pyramid_request, BearerTokenSchema
    ):
        pyramid_request.matchdict["id_"] = sentinel.id

        response = views.assignment_redirect_from_launch()

        BearerTokenSchema.return_value.authorization_param.assert_called_once_with(
            pyramid_request.lti_user
        )
        assert response == Any.instance_of(HTTPFound).with_attrs(
            {
                "location": "http://example.com/dashboard/assignment/sentinel.id",
            }
        )
        assert (
            response.headers["Set-Cookie"]
            == "authorization=TOKEN; Max-Age=86400; Path=/; expires=Tue, 02-Apr-2024 12:00:00 GMT; secure; HttpOnly"
        )

    @freeze_time("2024-04-01 12:00:00")
    @pytest.mark.usefixtures("BearerTokenSchema")
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
        assert (
            pyramid_request.response.headers["Set-Cookie"]
            == "authorization=TOKEN; Max-Age=86400; Path=/; expires=Tue, 02-Apr-2024 12:00:00 GMT; secure; HttpOnly"
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

    def test_get_request_assignment_404(
        self, pyramid_request, assignment_service, views
    ):
        pyramid_request.matchdict["id_"] = sentinel.id
        assignment_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            views.get_request_assignment()

    def test_get_request_assignment_403(
        self, pyramid_request, assignment_service, views
    ):
        pyramid_request.matchdict["id_"] = sentinel.id
        assignment_service.is_member.return_value = False

        with pytest.raises(HTTPUnauthorized):
            views.get_request_assignment()

    @pytest.fixture
    def BearerTokenSchema(self, patch):
        mock = patch("lms.views.dashboard.BearerTokenSchema")
        mock.return_value.authorization_param.return_value = "Bearer TOKEN"
        return mock

    @pytest.fixture
    def views(self, pyramid_request):
        return DashboardViews(pyramid_request)
