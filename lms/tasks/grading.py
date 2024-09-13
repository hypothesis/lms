from sqlalchemy import select, exists

from datetime import datetime
from lms.models import (
    GradingSyncGrade,
    GradingSync,
    LMSUser,
    LTIRegistration,
    Grouping,
    ApplicationInstance,
)
from lms.services import LTIAHTTPService
from lms.services.lti_grading.factory import LTI13GradingService
from lms.tasks.celery import app


@app.task()
def sync_grades():
    with app.request_context() as request:
        with request.tm:
            scheduled_syncs = request.db.scalars(
                select(GradingSync)
                .where(GradingSync.status == "scheduled")
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
                        grading_sync_timestamp=sync.created.isoformat(),
                    )

                sync.status = "in_progress"


@app.task()
def sync_grades_complete(*, grading_sync_id):
    with app.request_context() as request:
        with request.tm:
            grading_sync = request.db.get(GradingSync, grading_sync_id)

            result = request.db.execute(
                select(
                    ~exists(
                        select(GradingSyncGrade).where(
                            GradingSyncGrade.grading_sync_id == grading_sync_id,
                            GradingSyncGrade.success.is_(None),
                        )
                    ).label("completed"),
                    exists(
                        select(GradingSyncGrade).where(
                            GradingSyncGrade.grading_sync_id == grading_sync_id,
                            GradingSyncGrade.success == False,
                        )
                    ).label("failed"),
                )
            ).one()
            is_completed, is_failed = result.completed, result.failed

            if is_completed:
                grading_sync.status = "failed" if is_failed else "finished"


@app.task(
    max_retries=1,
    retry_backoff=10,
    autoretry_for=(Exception,),
)
def sync_grade(
    *,
    lti_registration_id,
    lis_outcome_service_url,
    grading_sync_timestamp,
    grading_sync_grade_id,
):
    with app.request_context() as request:
        with request.tm:
            grading_sync_grade = request.db.get(GradingSyncGrade, grading_sync_grade_id)

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
                    grading_sync_timestamp,
                    grading_sync_grade.lms_user.lti_v13_user_id,
                    grading_sync_grade.grade,
                )
            except Exception as err:
                if sync_grade.request.retries >= sync_grade.max_retries:
                    grading_sync_grade.success = False
                    grading_sync_grade.extra = str(err)
                    sync_grades_complete.delay(
                        grading_sync_id=grading_sync_grade.grading_sync.id
                    )
                    return

                raise

            grading_sync_grade.success = True
            sync_grades_complete.delay(
                grading_sync_id=grading_sync_grade.grading_sync.id
            )
