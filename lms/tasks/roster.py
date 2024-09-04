"""Celery tasks for fetching course rosters."""

from datetime import datetime, timedelta

from sqlalchemy import exists, select

from lms.models import (
    Assignment,
    AssignmentRoster,
    Course,
    CourseRoster,
    Event,
    LMSCourse,
)
from lms.services.roster import RosterService
from lms.tasks.celery import app

LAUNCHED_WINDOW = timedelta(hours=24)
"""How recent we need to have seen a launch from a course/assignment before we stop fetching rosters for it."""

ROSTER_REFRESH_WINDOW = timedelta(hours=24 * 7)
"""How frequenly should we fetch roster for the same course/assignment"""

ROSTER_LIMIT = 5
"""How many roster should we fetch per executing of the schedule task."""


@app.task()
def schedule_fetching_rosters() -> None:
    schedule_fetching_course_rosters()
    schedule_fetching_assignment_rosters()


def schedule_fetching_course_rosters() -> None:
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
            Event.timestamp >= now - LAUNCHED_WINDOW,
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
                # Schedule only a few rosters per call to this method
                .limit(ROSTER_LIMIT)
            )
            for lms_course_id in request.db.scalars(query).all():
                fetch_course_roster.delay(lms_course_id=lms_course_id)


def schedule_fetching_assignment_rosters() -> None:
    """Schedule fetching assignment rosters based on their last lunches and the most recent roster fetch."""

    # We use the python version (and not func.now()) for easier mocking during tests
    now = datetime.now()

    # Only fetch roster for assignments that don't have recent roster information
    no_recent_roster_clause = ~exists(
        select(AssignmentRoster).where(
            AssignmentRoster.assignment_id == Assignment.id,
            AssignmentRoster.updated >= now - ROSTER_REFRESH_WINDOW,
        )
    )

    # Only fetch rosters for assignments that have been recently launched
    recent_launches_cluase = exists(
        select(Event)
        .join(Assignment, Event.assignment_id == Assignment.id)
        .where(
            Event.timestamp >= now - LAUNCHED_WINDOW,
        )
    )

    with app.request_context() as request:
        with request.tm:
            query = (
                select(Assignment.id)
                .join(Course)
                .join(
                    LMSCourse,
                    LMSCourse.h_authority_provided_id == Course.authority_provided_id,
                )
                .where(
                    # Assignments that belongs to courses for which we have a LTIA membership service URL
                    LMSCourse.lti_context_memberships_url.is_not(None),
                    # Assignments for which we have stored the LTI1.3 ID
                    Assignment.lti_v13_resource_link_id.is_not(None),
                    no_recent_roster_clause,
                    recent_launches_cluase,
                )
                # Schedule only a few roster per call to this method
                .limit(ROSTER_LIMIT)
            )
            for assignment_id in request.db.scalars(query).all():
                fetch_assignment_roster.delay(assignment_id=assignment_id)


@app.task(
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=3600,
    retry_backoff_max=7200,
)
def fetch_course_roster(*, lms_course_id) -> None:
    """Fetch the roster for one course."""
    with app.request_context() as request:
        roster_service = request.find_service(RosterService)
        with request.tm:
            lms_course = request.db.get(LMSCourse, lms_course_id)
            roster_service.fetch_course_roster(lms_course)


@app.task(
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=3600,
    retry_backoff_max=7200,
)
def fetch_assignment_roster(*, assignment_id) -> None:
    """Fetch the roster for one course."""
    with app.request_context() as request:
        roster_service: RosterService = request.find_service(RosterService)
        with request.tm:
            assignment = request.db.get(Assignment, assignment_id)
            roster_service.fetch_assignment_roster(assignment)
