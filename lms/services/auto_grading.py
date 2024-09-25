from sqlalchemy import select

from lms.js_config_types import AnnotationMetrics
from lms.models import AutoGradingConfig, GradingSync, GradingSyncGrade, LMSUser


class AutoGradingService:
    def __init__(self, db):
        self._db = db

    def get_in_progress_sync(self, assignment) -> GradingSync | None:
        return self._db.scalars(
            self._search_query(
                assignment=assignment, statuses=["scheduled", "in_progress"]
            )
        ).one_or_none()

    def get_last_sync(self, assignment) -> GradingSync | None:
        return self._db.scalars(
            self._search_query(assignment=assignment).order_by(
                GradingSync.created.desc()
            )
        ).first()

    def create_grade_sync(
        self, assignment, created_by: LMSUser, grades: dict[LMSUser, float]
    ) -> GradingSync:
        grading_sync = GradingSync(
            assignment_id=assignment.id, created_by=created_by, status="scheduled"
        )
        self._db.add(grading_sync)
        self._db.flush()

        for lms_user, grade in grades.items():
            self._db.add(
                GradingSyncGrade(
                    grading_sync_id=grading_sync.id,
                    lms_user_id=lms_user.id,
                    grade=grade,
                )
            )

        return grading_sync

    def _search_query(self, assignment, statuses: list[str] | None = None):
        query = select(GradingSync).where(GradingSync.assignment_id == assignment.id)
        if statuses:
            query = query.where(GradingSync.status.in_(statuses))

        return query

    def calculate_grade(
        self,
        auto_grading_config: AutoGradingConfig,
        annotation_metrics: AnnotationMetrics,
    ) -> float:
        """Calculate auto grades based on the config and the number of annotations made.

        The results is a 100 based float rounded to two decimals.
        """
        combined_count = (
            annotation_metrics["annotations"] + annotation_metrics["replies"]
        )

        grade: float = 0
        match (
            auto_grading_config.grading_type,
            auto_grading_config.activity_calculation,
        ):
            case ("all_or_nothing", "cumulative"):
                if combined_count >= auto_grading_config.required_annotations:
                    grade = 100
                else:
                    grade = 0
            case ("all_or_nothing", "separate"):
                assert (
                    auto_grading_config.required_replies is not None
                ), "'separate' auto grade config with empty replies"
                if (
                    annotation_metrics["annotations"]
                    >= auto_grading_config.required_annotations
                    and annotation_metrics["replies"]
                    >= auto_grading_config.required_replies
                ):
                    grade = 100
                else:
                    grade = 0

            case ("scaled", "cumulative"):
                grade = combined_count / auto_grading_config.required_annotations * 100

            case ("scaled", "separate"):
                assert (
                    auto_grading_config.required_replies is not None
                ), "'separate' auto grade config with empty replies"
                # Let's make sure we do not count annotations or replies above the requirement, otherwise, a person
                # with 6 replies and 0 annotations on an assignment which requires 3 of each would get a 100% grade,
                # instead of 50%
                normalized_combined_count = min(
                    annotation_metrics["annotations"],
                    auto_grading_config.required_annotations,
                ) + min(
                    annotation_metrics["replies"], auto_grading_config.required_replies
                )
                grade = (
                    normalized_combined_count
                    / (
                        auto_grading_config.required_annotations
                        + auto_grading_config.required_replies
                    )
                    * 100
                )
            case _:
                raise ValueError("Unknown auto grading configuration")

        grade = min(100, grade)  # Proportional grades are capped at 100%
        return round(grade, 2)


def factory(_context, request):
    return AutoGradingService(db=request.db)
