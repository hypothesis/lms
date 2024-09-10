from datetime import datetime

import pytest
from freezegun import freeze_time

from lms.views.dashboard.api.grading import DashboardGradingViews
from tests import factories


@pytest.mark.usefixtures("dashboard_service", "ltia_http_service")
class TestDashboardGradingViews:
    @freeze_time("2022-06-21 12:00:00")
    def test_auto_grading_sync(
        self,
        lti_v13_application_instance,
        pyramid_request,
        views,
        DashboardGradingView,
        ltia_http_service,
        dashboard_service,
        assignment,
    ):
        dashboard_service.get_request_assignment.return_value = assignment

        views.auto_grading_sync()

        dashboard_service.get_request_assignment.assert_called_once_with(
            pyramid_request
        )
        DashboardGradingView.assert_called_once_with(
            ltia_service=ltia_http_service,
            line_item_url=None,
            line_item_container_url=None,
            product_family=None,
            misc_plugin=None,
            lti_registration=None,
        )
        DashboardGradingView.return_value.sync_grade.assert_called_once_with(
            lti_v13_application_instance.lti_registration,
            "LIS_OUTCOME_SERVICE_URL",
            datetime(2022, 6, 21, 12, 0, 0),
            "LTI_V13_USER_ID",
            1,
        )

    @pytest.fixture
    def assignment(self, lti_v13_application_instance, db_session):
        course = factories.Course(application_instance=lti_v13_application_instance)
        assignment = factories.Assignment(
            lis_outcome_service_url="LIS_OUTCOME_SERVICE_URL", course=course
        )
        db_session.flush()
        return assignment

    @pytest.fixture
    def lms_user(self):
        return factories.LMSUser(lti_v13_user_id="LTI_V13_USER_ID")

    @pytest.fixture
    def pyramid_request(self, pyramid_request, lms_user):
        pyramid_request.parsed_params = {
            "grades": [{"h_userid": lms_user.h_userid, "grade": 1}]
        }
        return pyramid_request

    @pytest.fixture
    def views(self, pyramid_request):
        return DashboardGradingViews(pyramid_request)

    @pytest.fixture
    def DashboardGradingView(self, patch):
        return patch("lms.views.dashboard.api.grading.LTI13GradingService")
