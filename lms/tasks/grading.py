from sqlalchemy import exists, select

from lms.models import (
    ApplicationInstance,
    GradingSync,
    GradingSyncGrade,
    Grouping,
    LTIRegistration,
)
from lms.services import LTIAHTTPService
from lms.services.lti_grading.factory import LTI13GradingService
from lms.tasks.celery import app


@app.task()
def sync_grades():
    """Start processing pending (scheduled) GradingSync."""
    with app.request_context() as request:
        with request.tm:
            scheduled_syncs = request.db.scalars(
                select(GradingSync)
                .where(GradingSync.status == "scheduled")
                # We'll call this task once per new GradingSync but if we find more pending ones also start those.
                .limit(5)
                .with_for_update()
            )

            for sync in scheduled_syncs:
                assignment = sync.assignment
                assert (
                    assignment.lis_outcome_service_url
                ), "Assignment without grading URL"
                lti_registration = request.db.scalars(
                    select(LTIRegistration)
                    .join(ApplicationInstance)
                    .join(Grouping)
                    .where(Grouping.id == assignment.course_id)
                    .order_by(LTIRegistration.updated.desc())
                ).first()
                assert lti_registration, "No LTI registraion for LTI1.3 assignment"

                for grade in sync.grades:
                    sync_grade.delay(
                        lti_registration_id=lti_registration.id,
                        lis_outcome_service_url=assignment.lis_outcome_service_url,
                        grading_sync_grade_id=grade.id,
                    )

                sync.status = "in_progress"


@app.task(
    max_retries=2,
    retry_backoff=10,
    autoretry_for=(Exception,),
)
def sync_grade(
    *, lti_registration_id, lis_outcome_service_url: str, grading_sync_grade_id: int
):
    """Send one particular grade to the LMS."""
    with app.request_context() as request:
        with request.tm:
            grading_sync_grade = request.db.get(GradingSyncGrade, grading_sync_grade_id)
            grading_sync = grading_sync_grade.grading_sync

            grading_service = LTI13GradingService(
                ltia_service=request.find_service(LTIAHTTPService),
                line_item_url=None,
                line_item_container_url=None,
                product_family=None,  # type: ignore
                misc_plugin=None,  # type: ignore
                lti_registration=None,  # type: ignore
            )
            try:
                grading_service.sync_grade(
                    request.db.get(LTIRegistration, lti_registration_id),
                    lis_outcome_service_url,
                    grading_sync.created.isoformat(),
                    grading_sync_grade.lms_user.lti_v13_user_id,
                    grading_sync_grade.grade,
                )
            except Exception as err:
                if sync_grade.request.retries >= sync_grade.max_retries:
                    # If this is the last retry, mark this particular grade as an error
                    grading_sync_grade.success = False
                    grading_sync_grade.error_details = {"exception": str(err)}

                    _schedule_sync_grades_complete(grading_sync.id, countdown=1)
                    return

                raise

            grading_sync_grade.success = True
            _schedule_sync_grades_complete(grading_sync.id, countdown=1)


@app.task()
def sync_grades_complete(*, grading_sync_id):
    """Summarize a GradingSync status based on the state of its children GradingSyncGrade."""
    with app.request_context() as request:
        with request.tm:
            grading_sync = request.db.get(GradingSync, grading_sync_id)

            result = request.db.execute(
                select(
                    # Are all GradingSyncGrade completed?
                    ~exists(
                        select(GradingSyncGrade).where(
                            GradingSyncGrade.grading_sync_id == grading_sync_id,
                            GradingSyncGrade.success.is_(None),
                        )
                    ).label("completed"),
                    # Are all GradingSyncGrade scucesfully?
                    exists(
                        select(GradingSyncGrade).where(
                            GradingSyncGrade.grading_sync_id == grading_sync_id,
                            GradingSyncGrade.success.is_(False),
                        )
                    ).label("failed"),
                )
            ).one()
            is_completed, is_failed = result.completed, result.failed

            if is_completed:
                grading_sync.status = "failed" if is_failed else "finished"


def _schedule_sync_grades_complete(grading_sync_id: int, countdown: int):
    sync_grades_complete.apply_async(
        (), {"grading_sync_id": grading_sync_id}, countdown=countdown
    )
