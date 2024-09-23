from unittest.mock import sentinel

import pytest

from lms.js_config_types import AnnotationMetrics
from lms.models import AutoGradingConfig
from lms.services.auto_grading import AutoGradingService, factory


class TestAutoGradingService:
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
    def svc(self):
        return AutoGradingService()


class TestFactory:
    def test_it(self, pyramid_request, AutoGradingService):
        service = factory(sentinel.context, pyramid_request)

        AutoGradingService.assert_called_once_with()
        assert service == AutoGradingService.return_value

    @pytest.fixture
    def AutoGradingService(self, patch):
        return patch("lms.services.auto_grading.AutoGradingService")
