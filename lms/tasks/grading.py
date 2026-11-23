import logging
from datetime import UTC

from sqlalchemy import exists, select

from lms.models import GradingSync, GradingSyncGrade
from lms.services.lti_grading.factory import service_factory
from lms.tasks.celery import app

LOG = logging.getLogger(__name__)


@app.task()
def sync_grades():
    """Start processing pending (scheduled) GradingSync."""
    with app.request_context() as request:  # noqa: SIM117
        with request.tm:
            scheduled_syncs = request.db.scalars(
                select(GradingSync)
                .where(GradingSync.status == "scheduled")
                # We'll call this task once per new GradingSync but if we find more pending ones also start those.
                .limit(5)
                .with_for_update()
            )

            for sync in scheduled_syncs:
                # Send one grade on its own and let it fan out the rest once
                # it lands.
                if lead_grade := min(
                    sync.grades, key=lambda grade: grade.id, default=None
                ):
                    sync_grade.delay(
                        grading_sync_grade_id=lead_grade.id, leads_sync=True
                    )

                sync.status = "in_progress"


@app.task(
    max_retries=2,
    retry_backoff=10,
    autoretry_for=(Exception,),
)
def sync_grade(*, grading_sync_grade_id: int, leads_sync: bool = False):
    """Send one particular grade to the LMS.

    :param leads_sync: whether the rest of this grade's GradingSync waits on
        it. D2L creates the assignment's grade item on the first score it
        receives, and duplicates it if several arrive at once.
    """
    with app.request_context() as request:  # noqa: SIM117
        with request.tm:
            grading_sync_grade = request.db.get(GradingSyncGrade, grading_sync_grade_id)
            grading_sync = grading_sync_grade.grading_sync
            assignment = grading_sync.assignment
            application_instance = assignment.course.application_instance
            grading_service = service_factory(None, request, application_instance)

            try:
                assert assignment.lis_outcome_service_url, (  # noqa: S101
                    "Assignment without grading URL"
                )

                grading_service.sync_grade(
                    application_instance,
                    assignment,
                    # DB dates are not TZ aware but are always in UTC
                    # Make them TZ aware so the LTI API calls have an explicit timezone
                    grading_sync.created.replace(tzinfo=UTC).isoformat(),
                    grading_sync_grade.lms_user,
                    grading_sync_grade.grade,
                )
            except Exception as err:
                if sync_grade.request.retries >= sync_grade.max_retries:
                    # If this is the last retry, mark this particular grade as an error
                    grading_sync_grade.success = False
                    grading_sync_grade.error_details = {"exception": str(err)}
                    if leads_sync and (
                        remaining := _remaining_grades(grading_sync, grading_sync_grade)
                    ):
                        # Nothing reached the LMS, so the grade item may still
                        # be missing and the rest can't go out together yet.
                        # Hand the lead to the next one instead.
                        sync_grade.delay(
                            grading_sync_grade_id=remaining[0].id, leads_sync=True
                        )
                    _schedule_sync_grades_complete(grading_sync.id, countdown=1)
                    LOG.exception("Syncing grade back to LMS failed")
                    return

                raise

            grading_sync_grade.success = True
            if leads_sync:
                for grade in _remaining_grades(grading_sync, grading_sync_grade):
                    sync_grade.delay(grading_sync_grade_id=grade.id)
            _schedule_sync_grades_complete(grading_sync.id, countdown=1)


@app.task()
def sync_grades_complete(*, grading_sync_id):
    """Summarize a GradingSync status based on the state of its children GradingSyncGrade."""
    with app.request_context() as request:  # noqa: SIM117
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


def _remaining_grades(
    grading_sync: GradingSync, synced_grade: GradingSyncGrade
) -> list[GradingSyncGrade]:
    """Get the GradingSync's grades that haven't been sent yet, in send order."""
    return sorted(
        (
            grade
            for grade in grading_sync.grades
            if grade.id != synced_grade.id and grade.success is None
        ),
        key=lambda grade: grade.id,
    )


def _schedule_sync_grades_complete(grading_sync_id: int, countdown: int):
    sync_grades_complete.apply_async(
        (), {"grading_sync_id": grading_sync_id}, countdown=countdown
    )
