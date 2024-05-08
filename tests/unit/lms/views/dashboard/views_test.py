from unittest.mock import create_autospec, sentinel

import pytest
from freezegun import freeze_time
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound

from lms.resources._js_config import JSConfig
from lms.resources.dashboard import DashboardResource
from lms.views.dashboard.views import DashboardViews

pytestmark = pytest.mark.usefixtures("h_api", "assignment_service")


# pylint:disable=protected-access
class TestDashboardViews:
    @freeze_time("2024-04-01 12:00:00")
    def test_assignment_redirect_from_launch(
        self, views, pyramid_request, BearerTokenSchema, organization
    ):
        pyramid_request.matchdict["id_"] = sentinel.id

        response = views.assignment_redirect_from_launch()

        BearerTokenSchema.return_value.authorization_param.assert_called_once_with(
            pyramid_request.lti_user
        )
        assert response == Any.instance_of(HTTPFound).with_attrs(
            {
                "location": f"http://example.com/dashboard/organization/{organization._public_id}/assignment/sentinel.id",
            }
        )
        assert (
            response.headers["Set-Cookie"]
            == f"authorization=TOKEN; Max-Age=86400; Path=/dashboard/organization/{organization._public_id}; expires=Tue, 02-Apr-2024 12:00:00 GMT; secure; HttpOnly"
        )

    @freeze_time("2024-04-01 12:00:00")
    @pytest.mark.usefixtures("BearerTokenSchema")
    def test_assignment_show(
        self, views, pyramid_request, assignment_service, organization, config
    ):
        context = DashboardResource(pyramid_request)
        context.js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        pyramid_request.context = context
        pyramid_request.matchdict["id_"] = sentinel.id

        views.assignment_show()

        assignment_service.get_by_id.assert_called_once_with(sentinel.id)
        pyramid_request.context.js_config.enable_dashboard_mode.assert_called_once_with(
            config
        )
        assert (
            pyramid_request.response.headers["Set-Cookie"]
            == f"authorization=TOKEN; Max-Age=86400; Path=/dashboard/organization/{organization._public_id}; expires=Tue, 02-Apr-2024 12:00:00 GMT; secure; HttpOnly"
        )

    def test_assignment_show_with_no_lti_user(
        self, views, pyramid_request, assignment_service, config
    ):
        context = DashboardResource(pyramid_request)
        context.js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        pyramid_request.context = context
        pyramid_request.lti_user = None
        pyramid_request.matchdict["id_"] = sentinel.id

        views.assignment_show()

        assignment_service.get_by_id.assert_called_once_with(sentinel.id)
        pyramid_request.context.js_config.enable_dashboard_mode.assert_called_once_with(
            config
        )

    @pytest.fixture
    def config(self):
        return {
            "links": {
                "assignmentApi": "/dashboard/api/assignment/:id_",
                "assignmentStatsApi": "/dashboard/api/assignment/:id_/stats",
            }
        }

    @pytest.fixture
    def BearerTokenSchema(self, patch):
        mock = patch("lms.views.dashboard.views.BearerTokenSchema")
        mock.return_value.authorization_param.return_value = "Bearer TOKEN"
        return mock

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config):
        pyramid_config.testing_securitypolicy(permissive=False)
        return pyramid_config

    @pytest.fixture
    def views(self, pyramid_request):
        return DashboardViews(pyramid_request)
