"""Celery tasks for fetching course rosters."""

from lms.models import LMSCourse
from lms.services.course_roster import CourseRosterService
from lms.tasks.celery import app


@app.task(
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=3600,
    retry_backoff_max=7200,
)
def fetch_roster(*, lms_course_id) -> None:
    """Fetch the roster for one course."""

    with app.request_context() as request:
        roster_service = request.find_service(CourseRosterService)
        with request.tm:
            lms_course = request.db.get(LMSCourse, lms_course_id)
            roster_service.fetch_roster(lms_course)
