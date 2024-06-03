# ruff: noqa: SLF001
from unittest.mock import create_autospec, sentinel

import pytest
from freezegun import freeze_time
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound

from lms.resources._js_config import JSConfig
from lms.resources.dashboard import DashboardResource
from lms.views.dashboard.views import DashboardViews

pytestmark = pytest.mark.usefixtures(
    "h_api", "assignment_service", "course_service", "organization_service"
)


class TestDashboardViews:
    @freeze_time("2024-04-01 12:00:00")
    def test_assignment_redirect_from_launch(
        self, views, pyramid_request, BearerTokenSchema, organization
    ):
        pyramid_request.matchdict["assignment_id"] = sentinel.id

        response = views.assignment_redirect_from_launch()

        BearerTokenSchema.return_value.authorization_param.assert_called_once_with(
            pyramid_request.lti_user
        )
        assert response == Any.instance_of(HTTPFound).with_attrs(
            {
                "location": f"http://example.com/dashboard/organizations/{organization._public_id}/assignments/sentinel.id",
            }
        )
        assert (
            response.headers["Set-Cookie"]
            == f"authorization=TOKEN; Max-Age=86400; Path=/dashboard/organizations/{organization._public_id}; expires=Tue, 02-Apr-2024 12:00:00 GMT; secure; HttpOnly"
        )

    @freeze_time("2024-04-01 12:00:00")
    @pytest.mark.usefixtures("BearerTokenSchema")
    def test_assignment_show(
        self, views, pyramid_request, assignment_service, organization
    ):
        context = DashboardResource(pyramid_request)
        context.js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        pyramid_request.context = context
        pyramid_request.matchdict["assignment_id"] = sentinel.id

        views.assignment_show()

        assignment_service.get_by_id.assert_called_once_with(sentinel.id)
        pyramid_request.context.js_config.enable_dashboard_mode.assert_called_once()
        assert (
            pyramid_request.response.headers["Set-Cookie"]
            == f"authorization=TOKEN; Max-Age=86400; Path=/dashboard/organizations/{organization._public_id}; expires=Tue, 02-Apr-2024 12:00:00 GMT; secure; HttpOnly"
        )

    @freeze_time("2024-04-01 12:00:00")
    @pytest.mark.usefixtures("BearerTokenSchema")
    def test_course_show(self, views, pyramid_request, course_service, organization):
        context = DashboardResource(pyramid_request)
        context.js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        pyramid_request.context = context
        pyramid_request.matchdict["course_id"] = sentinel.id

        views.course_show()

        course_service.get_by_id.assert_called_once_with(sentinel.id)
        pyramid_request.context.js_config.enable_dashboard_mode.assert_called_once()
        assert (
            pyramid_request.response.headers["Set-Cookie"]
            == f"authorization=TOKEN; Max-Age=86400; Path=/dashboard/organizations/{organization._public_id}; expires=Tue, 02-Apr-2024 12:00:00 GMT; secure; HttpOnly"
        )

    @freeze_time("2024-04-01 12:00:00")
    @pytest.mark.usefixtures("BearerTokenSchema")
    def test_organization_show(
        self,
        views,
        pyramid_request,
        organization_service,
        organization,
        get_request_organization,
    ):
        context = DashboardResource(pyramid_request)
        context.js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        pyramid_request.context = context

        views.organization_show()

        get_request_organization.assert_called_once_with(
            pyramid_request, organization_service
        )
        pyramid_request.context.js_config.enable_dashboard_mode.assert_called_once()
        assert (
            pyramid_request.response.headers["Set-Cookie"]
            == f"authorization=TOKEN; Max-Age=86400; Path=/dashboard/organizations/{organization._public_id}; expires=Tue, 02-Apr-2024 12:00:00 GMT; secure; HttpOnly"
        )

    def test_assignment_show_with_no_lti_user(
        self, views, pyramid_request, assignment_service
    ):
        context = DashboardResource(pyramid_request)
        context.js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        pyramid_request.context = context
        pyramid_request.lti_user = None
        pyramid_request.matchdict["assignment_id"] = sentinel.id

        views.assignment_show()

        assignment_service.get_by_id.assert_called_once_with(sentinel.id)
        pyramid_request.context.js_config.enable_dashboard_mode.assert_called_once()

    @pytest.fixture
    def BearerTokenSchema(self, patch):
        mock = patch("lms.views.dashboard.views.BearerTokenSchema")
        mock.return_value.authorization_param.return_value = "Bearer TOKEN"
        return mock

    @pytest.fixture
    def get_request_organization(self, patch):
        return patch("lms.views.dashboard.views.get_request_organization")

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config):
        pyramid_config.testing_securitypolicy(permissive=False)
        return pyramid_config

    @pytest.fixture
    def views(self, pyramid_request):
        return DashboardViews(pyramid_request)
