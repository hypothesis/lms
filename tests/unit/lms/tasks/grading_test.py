from contextlib import contextmanager
from datetime import UTC
from unittest.mock import call

import pytest

from lms.tasks.grading import sync_grade, sync_grades, sync_grades_complete
from tests import factories


class TestGradingTasks:
    def test_sync_grades(self, sync_grade, grading_sync):
        sync_grades()

        sync_grade.delay.assert_has_calls(
            [
                call(lis_outcome_service_url="URL", grading_sync_grade_id=grade.id)
                for grade in grading_sync.grades
            ],
            any_order=True,
        )
        assert grading_sync.status == "in_progress"

    def test_sync_grade(
        self,
        grading_sync,
        lti_v13_application_instance,
        service_factory,
        pyramid_request,
        sync_grades_complete,
    ):
        sync_grade(
            lis_outcome_service_url="URL",
            grading_sync_grade_id=grading_sync.grades[0].id,
        )

        service_factory.assert_called_once_with(
            None, pyramid_request, lti_v13_application_instance
        )
        grading_service = service_factory.return_value

        grading_service.sync_grade.assert_called_once_with(
            lti_v13_application_instance,
            "URL",
            grading_sync.created.replace(tzinfo=UTC).isoformat(),
            grading_sync.grades[0].lms_user,
            grading_sync.grades[0].grade,
        )
        sync_grades_complete.apply_async.assert_called_once_with(
            (), {"grading_sync_id": grading_sync.id}, countdown=1
        )
        assert grading_sync.grades[0].success is True

    @pytest.mark.usefixtures("ltia_http_service")
    def test_sync_grade_raises(
        self, grading_sync, service_factory, sync_grades_complete
    ):
        grading_service = service_factory.return_value
        grading_service.sync_grade.side_effect = Exception
        sync_grade.max_retries = 2

        with pytest.raises(Exception):
            sync_grade(
                lis_outcome_service_url="URL",
                grading_sync_grade_id=grading_sync.grades[0].id,
            )

        sync_grades_complete.apply_async.assert_not_called()
        assert grading_sync.grades[0].success is None

    @pytest.mark.usefixtures("ltia_http_service")
    def test_sync_grade_last_retry(
        self, grading_sync, service_factory, sync_grades_complete
    ):
        grading_service = service_factory.return_value
        grading_service.sync_grade.side_effect = Exception
        sync_grade.max_retries = 0

        sync_grade(
            lis_outcome_service_url="URL",
            grading_sync_grade_id=grading_sync.grades[0].id,
        )

        sync_grades_complete.apply_async.assert_called_once_with(
            (), {"grading_sync_id": grading_sync.id}, countdown=1
        )
        assert grading_sync.grades[0].success is False
        assert grading_sync.grades[0].error_details == {"exception": str(Exception())}

    @pytest.mark.parametrize(
        "success_values,status",
        [
            ((None, None), "in_progress"),
            ((None, False), "in_progress"),
            ((None, True), "in_progress"),
            ((True, True), "finished"),
            ((False, True), "failed"),
        ],
    )
    def test_syn_grades_complete(self, grading_sync, success_values, status):
        grading_sync.grades[0].success, grading_sync.grades[1].success = success_values

        sync_grades_complete(grading_sync_id=grading_sync.id)

        grading_sync.status = status

    @pytest.fixture
    def assignment(self, lti_v13_application_instance):
        course = factories.Course(application_instance=lti_v13_application_instance)
        return factories.Assignment(lis_outcome_service_url="URL", course=course)

    @pytest.fixture
    def grading_sync(self, assignment, db_session):
        grading_sync = factories.GradingSync(assignment=assignment, status="scheduled")
        db_session.flush()
        factories.GradingSyncGrade(
            grading_sync=grading_sync, lms_user=factories.LMSUser(), grade=0.5
        )
        factories.GradingSyncGrade(
            grading_sync=grading_sync, lms_user=factories.LMSUser(), grade=1
        )
        db_session.flush()
        return grading_sync

    @pytest.fixture
    def sync_grade(self, patch):
        return patch("lms.tasks.grading.sync_grade")

    @pytest.fixture
    def sync_grades_complete(self, patch):
        return patch("lms.tasks.grading.sync_grades_complete")

    @pytest.fixture
    def service_factory(self, patch):
        return patch("lms.tasks.grading.service_factory")


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.grading.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
