from lms.js_config_types import AnnotationMetrics
from sqlalchemy import select
from lms.models import AutoGradingConfig, GradingSync, GradingSyncGrade, LMSUser


def calculate_grade(
    auto_grading_config: AutoGradingConfig, annotation_metrics: AnnotationMetrics
) -> float:
    """Calculate auto grades based on the config and the number of annotations made.

    The results is a 100 based float rounded to two decimals.
    """
    combined_count = annotation_metrics["annotations"] + annotation_metrics["replies"]

    grade: float = 0
    match (auto_grading_config.grading_type, auto_grading_config.activity_calculation):
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
            grade = (
                combined_count
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


def get_last_synced_grade_for_h_userids(db, h_userids: list[str], assignment_id):
    result = db.execute(
        select(LMSUser.h_userid, GradingSyncGrade.grade)
        .distinct(LMSUser.h_userid)
        .join(GradingSync)
        .join(LMSUser)
        .where(
            GradingSync.assignment_id == assignment_id,
            GradingSyncGrade.success == True,
            LMSUser.h_userid.in_(h_userids),
        )
        .order_by(LMSUser.h_userid, GradingSyncGrade.updated.desc())
    ).all()
    print(result)

    return {r[0]: r[1] for r in result}
