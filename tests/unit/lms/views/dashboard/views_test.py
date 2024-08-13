from datetime import timedelta
from unittest.mock import create_autospec, sentinel

import pytest
from freezegun import freeze_time
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound

from lms.resources._js_config import JSConfig
from lms.resources.dashboard import DashboardResource
from lms.views.dashboard.views import AUTHORIZATION_DURATION_SECONDS, DashboardViews

pytestmark = pytest.mark.usefixtures(
    "h_api",
    "assignment_service",
    "course_service",
    "organization_service",
    "dashboard_service",
)


class TestDashboardViews:
    @freeze_time("2024-04-01 12:00:00")
    def test_assignment_redirect_from_launch(
        self, views, pyramid_request, BearerTokenSchema
    ):
        pyramid_request.matchdict["assignment_id"] = sentinel.id

        response = views.assignment_redirect_from_launch()

        BearerTokenSchema.return_value.authorization_param.assert_called_once_with(
            pyramid_request.lti_user,
            lifetime=timedelta(seconds=AUTHORIZATION_DURATION_SECONDS),
        )
        assert response == Any.instance_of(HTTPFound).with_attrs(
            {"location": "http://example.com/dashboard/assignments/sentinel.id/"}
        )
        self.assert_cookie_value(response)

    @freeze_time("2024-04-01 12:00:00")
    @pytest.mark.usefixtures("BearerTokenSchema")
    def test_assignment_show(self, views, pyramid_request, dashboard_service):
        context = DashboardResource(pyramid_request)
        context.js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        pyramid_request.context = context
        pyramid_request.matchdict["assignment_id"] = sentinel.id

        views.assignment_show()

        dashboard_service.get_request_assignment.assert_called_once_with(
            pyramid_request
        )
        pyramid_request.context.js_config.enable_dashboard_mode.assert_called_once()
        self.assert_cookie_value(pyramid_request.response)

    @freeze_time("2024-04-01 12:00:00")
    @pytest.mark.usefixtures("BearerTokenSchema")
    def test_course_show(self, views, pyramid_request, dashboard_service):
        context = DashboardResource(pyramid_request)
        context.js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        pyramid_request.context = context
        pyramid_request.matchdict["course_id"] = sentinel.id

        views.course_show()

        dashboard_service.get_request_course.assert_called_once_with(pyramid_request)
        pyramid_request.context.js_config.enable_dashboard_mode.assert_called_once()
        self.assert_cookie_value(pyramid_request.response)

    @freeze_time("2024-04-01 12:00:00")
    @pytest.mark.usefixtures("BearerTokenSchema")
    def test_organization_show(self, views, pyramid_request):
        context = DashboardResource(pyramid_request)
        context.js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        pyramid_request.context = context

        views.courses()

        pyramid_request.context.js_config.enable_dashboard_mode.assert_called_once()
        self.assert_cookie_value(pyramid_request.response)

    def test_assignment_show_with_no_lti_user(
        self, views, pyramid_request, dashboard_service
    ):
        context = DashboardResource(pyramid_request)
        context.js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        pyramid_request.context = context
        pyramid_request.lti_user = None
        pyramid_request.matchdict["assignment_id"] = sentinel.id

        views.assignment_show()

        dashboard_service.get_request_assignment.assert_called_once_with(
            pyramid_request
        )
        pyramid_request.context.js_config.enable_dashboard_mode.assert_called_once()

    def assert_cookie_value(self, response):
        assert (
            response.headers["Set-Cookie"]
            == f"authorization=TOKEN; Max-Age={AUTHORIZATION_DURATION_SECONDS}; Path=/dashboard; expires=Mon, 08-Apr-2024 12:00:00 GMT; secure; HttpOnly"
        )

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
