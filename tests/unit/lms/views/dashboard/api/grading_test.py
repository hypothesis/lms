from unittest.mock import Mock

import pytest
from pyramid.httpexceptions import HTTPNotFound

from lms.views.dashboard.api.grading import DashboardGradingViews
from tests import factories


@pytest.mark.usefixtures(
    "dashboard_service", "ltia_http_service", "auto_grading_service"
)
class TestDashboardGradingViews:
    def test_create_grading_sync_with_existing_sync(
        self,
        pyramid_request,
        views,
        auto_grading_service,
        dashboard_service,
        assignment,
    ):
        dashboard_service.get_request_assignment.return_value = assignment

        views.create_grading_sync()

        dashboard_service.get_request_assignment.assert_called_once_with(
            pyramid_request
        )
        auto_grading_service.get_in_progress_sync.assert_called_once_with(
            dashboard_service.get_request_assignment.return_value
        )
        pyramid_request.response.status_int = 400

    def test_create_grading_sync(
        self,
        pyramid_request,
        views,
        auto_grading_service,
        dashboard_service,
        assignment,
        db_session,
    ):
        pyramid_request.parsed_params["grades"] = [
            {"h_userid": "STUDENT_1", "grade": 0.5},
            {"h_userid": "STUDENT_2", "grade": 1},
        ]
        dashboard_service.get_request_assignment.return_value = assignment
        auto_grading_service.get_in_progress_sync.return_value = None
        student_1 = factories.LMSUser(h_userid="STUDENT_1")
        student_2 = factories.LMSUser(h_userid="STUDENT_2")
        db_session.flush()

        response = views.create_grading_sync()

        dashboard_service.get_request_assignment.assert_called_once_with(
            pyramid_request
        )
        auto_grading_service.get_in_progress_sync.assert_called_once_with(
            dashboard_service.get_request_assignment.return_value
        )
        auto_grading_service.create_grade_sync.assert_called_once_with(
            dashboard_service.get_request_assignment.return_value,
            pyramid_request.user.lms_user,
            {student_1: 0.5, student_2: 1},
        )
        assert response == {
            "status": auto_grading_service.create_grade_sync.return_value.status
        }
        pyramid_request.add_finished_callback.assert_called_once_with(
            views._start_sync_grades  # noqa: SLF001
        )

    def test_get_grading_sync(
        self, auto_grading_service, pyramid_request, views, dashboard_service
    ):
        response = views.get_grading_sync()

        dashboard_service.get_request_assignment.assert_called_once_with(
            pyramid_request
        )
        auto_grading_service.get_last_sync.assert_called_once_with(
            dashboard_service.get_request_assignment.return_value
        )
        assert response == {
            "status": auto_grading_service.get_last_sync.return_value.status
        }

    def test_get_grading_sync_not_found(self, auto_grading_service, views):
        auto_grading_service.get_last_sync.return_value = None

        with pytest.raises(HTTPNotFound):
            views.get_grading_sync()

    def test__start_sync_grades(self, sync_grades, views, pyramid_request):
        views._start_sync_grades(pyramid_request)  # noqa: SLF001

        sync_grades.delay.assert_called_once_with()

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
        pyramid_request.add_finished_callback = Mock()
        return pyramid_request

    @pytest.fixture
    def views(self, pyramid_request):
        return DashboardGradingViews(pyramid_request)

    @pytest.fixture
    def sync_grades(self, patch):
        return patch("lms.views.dashboard.api.grading.sync_grades")