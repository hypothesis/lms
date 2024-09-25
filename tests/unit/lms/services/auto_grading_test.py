import random
from datetime import datetime
from unittest.mock import sentinel

import pytest

from lms.js_config_types import AnnotationMetrics
from lms.models import AutoGradingConfig
from lms.services.auto_grading import AutoGradingService, factory
from tests import factories


class TestAutoGradingService:
    @pytest.mark.parametrize("status", ["scheduled", "in_progress"])
    @pytest.mark.usefixtures("failed_grading_sync")
    def test_get_in_progress_sync_existing(self, svc, db_session, status, assignment):
        grading_sync = factories.GradingSync(assignment=assignment, status=status)
        db_session.flush()

        assert svc.get_in_progress_sync(assignment) == grading_sync

    def test_get_in_progress_sync(self, svc, db_session):
        assignment = factories.Assignment()
        db_session.flush()

        assert not svc.get_in_progress_sync(assignment)

    def test_get_last_sync(self, svc, db_session, assignment):
        factories.GradingSync(assignment=assignment, created=datetime(2020, 1, 1))
        new = factories.GradingSync(assignment=assignment, created=datetime(2024, 1, 1))
        db_session.flush()

        assert svc.get_last_sync(assignment) == new

    def test_create_grade_sync(self, svc, db_session, assignment):
        creator = factories.LMSUser()
        lms_users = factories.LMSUser.create_batch(5)
        grades = {lms_user: random.random() for lms_user in lms_users}
        db_session.flush()

        grading_sync = svc.create_grade_sync(assignment, creator, grades)

        assert grading_sync.status == "scheduled"
        assert grading_sync.assignment == assignment
        assert grading_sync.created_by == creator
        for grade in grading_sync.grades:
            assert grade.grade == grades[grade.lms_user]

    def test_get_last_grades(self, svc, db_session, assignment):
        student = factories.LMSUser()

        sync = factories.GradingSync(assignment=assignment)

        # Not successful
        factories.GradingSyncGrade(
            grading_sync=sync,
            lms_user=student,
            success=False,
            updated=datetime(2025, 1, 1),
            grade=1,
        )
        # Old
        factories.GradingSyncGrade(
            grading_sync=sync,
            lms_user=student,
            success=True,
            updated=datetime(2023, 1, 1),
            grade=2,
        )
        factories.GradingSyncGrade(
            grading_sync=sync,
            lms_user=student,
            success=True,
            updated=datetime(2024, 1, 1),
            grade=3,
        )
        db_session.flush()

        last_grades = svc.get_last_grades(assignment, success=True)

        assert last_grades.get(student.h_userid).grade == 3

    @pytest.mark.parametrize(
        "grading_type,activity_calculation,required_annotations, required_replies,annotations,replies,expected_grade",
        [
            ("all_or_nothing", "cumulative", 15, None, 5, 5, 0),
            ("all_or_nothing", "cumulative", 15, None, 10, 6, 100),
            ("all_or_nothing", "separate", 10, 5, 10, 4, 0),
            ("all_or_nothing", "separate", 10, 5, 10, 5, 100),
            ("scaled", "cumulative", 15, None, 5, 5, 66.67),
            ("scaled", "cumulative", 15, None, 10, 10, 100),
            ("scaled", "separate", 10, 5, 8, 2, 66.67),
            ("scaled", "separate", 10, 5, 5, 1, 40),
            # In scaled+separate cases, extra annos/replies should be ignored
            ("scaled", "separate", 3, 2, 0, 3, 40),
            ("scaled", "separate", 5, 5, 12, 2, 70),
        ],
    )
    def test_calculate_grade(
        self,
        activity_calculation,
        grading_type,
        required_annotations,
        required_replies,
        annotations,
        replies,
        expected_grade,
        svc,
    ):
        grade = svc.calculate_grade(
            AutoGradingConfig(
                activity_calculation=activity_calculation,
                grading_type=grading_type,
                required_annotations=required_annotations,
                required_replies=required_replies,
            ),
            AnnotationMetrics(annotations=annotations, replies=replies),
        )

        assert grade == expected_grade

    def test_calculate_grade_bad_config(self, svc):
        with pytest.raises(ValueError):
            svc.calculate_grade(
                AutoGradingConfig(
                    activity_calculation="RANDOM",
                    grading_type="RANDOM",
                    required_annotations=10,
                    required_replies=10,
                ),
                AnnotationMetrics(annotations=10, replies=10),
            )

    @pytest.fixture
    def assignment(self):
        return factories.Assignment()

    @pytest.fixture
    def failed_grading_sync(self, assignment):
        return factories.GradingSync(assignment=assignment, status="failed")

    @pytest.fixture
    def svc(self, db_session):
        return AutoGradingService(db_session)


class TestFactory:
    def test_it(self, pyramid_request, db_session, AutoGradingService):
        service = factory(sentinel.context, pyramid_request)

        AutoGradingService.assert_called_once_with(db=db_session)
        assert service == AutoGradingService.return_value

    @pytest.fixture
    def AutoGradingService(self, patch):
        return patch("lms.services.auto_grading.AutoGradingService")
