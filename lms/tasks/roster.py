"""Celery tasks for fetching course rosters."""

from datetime import datetime, timedelta

from sqlalchemy import exists, select

from lms.models import Course, CourseRoster, Event, LMSCourse
from lms.services.roster import RosterService
from lms.tasks.celery import app

COURSE_LAUNCHED_WINDOW = timedelta(hours=24)
"""How recent we need to have seen a launch from a course before we stop fetching rosters for it."""

ROSTER_REFRESH_WINDOW = timedelta(hours=24 * 7)
"""How frequenly should we fetch roster for the same course"""

ROSTER_COURSE_LIMIT = 5
"""How many roster should we fetch per executing of the schedule task."""


@app.task()
def schedule_fetching_rosters() -> None:
    """Schedule fetching course rosters based on their last lunches and the most recent roster fetch."""

    # We use the python version (and not func.now()) for easier mocking during tests
    now = datetime.now()

    # Only fetch roster for courses that don't have recent roster information
    no_recent_roster_clause = ~exists(
        select(CourseRoster).where(
            CourseRoster.lms_course_id == LMSCourse.id,
            CourseRoster.updated >= now - ROSTER_REFRESH_WINDOW,
        )
    )

    # Only fetch rosters for courses that have been recently launched
    recent_launches_cluase = exists(
        select(Event)
        .join(Course, Event.course_id == Course.id)
        .where(
            Event.timestamp >= now - COURSE_LAUNCHED_WINDOW,
            Course.authority_provided_id == LMSCourse.h_authority_provided_id,
        )
    )

    with app.request_context() as request:
        with request.tm:
            query = (
                select(LMSCourse.id)
                .where(
                    # Courses for which we have a LTIA membership service URL
                    LMSCourse.lti_context_memberships_url.is_not(None),
                    no_recent_roster_clause,
                    recent_launches_cluase,
                )
                # Schedule only a few roster per call to this method
                .limit(ROSTER_COURSE_LIMIT)
            )
            for lms_course_id in request.db.scalars(query).all():
                fetch_roster.delay(lms_course_id=lms_course_id)


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
        roster_service = request.find_service(RosterService)
        with request.tm:
            lms_course = request.db.get(LMSCourse, lms_course_id)
            roster_service.fetch_roster(lms_course)
