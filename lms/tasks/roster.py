"""Celery tasks for fetching course rosters."""

from datetime import datetime, timedelta

from sqlalchemy import exists, func, select

from lms.models import (
    Assignment,
    AssignmentRoster,
    Course,
    CourseRoster,
    Event,
    LMSCourse,
    LMSSegment,
    LMSSegmentRoster,
    TaskDone,
)
from lms.services.roster import RosterService
from lms.tasks.celery import app

LAUNCHED_WINDOW = timedelta(hours=24)
"""How recent we need to have seen a launch from a course/assignment before we stop fetching rosters for it."""

ROSTER_REFRESH_WINDOW = timedelta(hours=24 * 3)
"""How frequenly should we fetch roster for the same course/assignment/segment"""

ROSTER_LIMIT = 50
"""How many rosters should we fetch per execution of the schedule task."""


@app.task()
def schedule_fetching_rosters() -> None:
    schedule_fetching_course_rosters()
    schedule_fetching_assignment_rosters()
    schedule_fetching_segment_rosters()


def schedule_fetching_course_rosters() -> None:
    """Schedule fetching course rosters based on their last lunches and the most recent roster fetch."""

    # We use the python version (and not func.now()) for easier mocking during tests
    now = datetime.now()  # noqa: DTZ005

    # Only fetch roster for courses for which we haven't schedule a fetch recently
    no_recent_scheduled_roster_fetch_clause = ~exists(
        select(TaskDone).where(
            TaskDone.key == func.concat("roster::course::scheduled::", LMSCourse.id),
        )
    )

    # Only fetch roster for courses that don't have recent roster information
    no_recent_roster_clause = ~exists(
        select(CourseRoster).where(
            CourseRoster.lms_course_id == LMSCourse.id,
            CourseRoster.updated >= now - ROSTER_REFRESH_WINDOW,
        )
    )

    # Only fetch rosters for courses that have been recently launched
    recent_launches_clause = exists(
        select(Event)
        .join(Course, Event.course_id == Course.id)
        .where(
            Event.timestamp >= now - LAUNCHED_WINDOW,
            Course.authority_provided_id == LMSCourse.h_authority_provided_id,
        )
    )

    with app.request_context() as request:  # noqa: SIM117
        with request.tm:
            query = (
                select(LMSCourse.id)
                .where(
                    # Courses for which we have a LTIA membership service URL
                    LMSCourse.lti_context_memberships_url.is_not(None),
                    no_recent_roster_clause,
                    no_recent_scheduled_roster_fetch_clause,
                    recent_launches_clause,
                )
                # Prefer newer courses
                .order_by(LMSCourse.created.desc())
                # Schedule only a few rosters per call to this method
                .limit(ROSTER_LIMIT)
            )
            for lms_course_id in request.db.scalars(query).all():
                fetch_course_roster.delay(lms_course_id=lms_course_id)
                # Record that the roster fetching has been scheduled
                # We set the expiration date to ROSTER_REFRESH_WINDOW so we'll try again after that period
                request.db.add(
                    TaskDone(
                        key=f"roster::course::scheduled::{lms_course_id}",
                        data=None,
                        expires_at=datetime.now() + ROSTER_REFRESH_WINDOW,  # noqa: DTZ005
                    )
                )


def schedule_fetching_assignment_rosters() -> None:
    """Schedule fetching assignment rosters based on their last lunches and the most recent roster fetch."""

    # We use the python version (and not func.now()) for easier mocking during tests
    now = datetime.now()  # noqa: DTZ005

    no_recent_roster_clause = ~exists(
        select(AssignmentRoster).where(
            AssignmentRoster.assignment_id == Assignment.id,
            AssignmentRoster.updated >= now - ROSTER_REFRESH_WINDOW,
        )
    )

    no_recent_scheduled_roster_fetch_clause = ~exists(
        select(TaskDone).where(
            TaskDone.key
            == func.concat("roster::assignment::scheduled::", Assignment.id),
        )
    )

    # Only fetch rosters for assignments that have been recently launched
    recent_launches_clause = exists(
        select(Event).where(
            Event.assignment_id == Assignment.id,
            Event.timestamp >= now - LAUNCHED_WINDOW,
        )
    )

    with app.request_context() as request:  # noqa: SIM117
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
                    no_recent_scheduled_roster_fetch_clause,
                    no_recent_roster_clause,
                    recent_launches_clause,
                )
                # Prefer newer assignments
                .order_by(Assignment.created.desc())
                # Schedule only a few roster per call to this method
                .limit(ROSTER_LIMIT)
            )
            for assignment_id in request.db.scalars(query).all():
                fetch_assignment_roster.delay(assignment_id=assignment_id)
                # Record that the roster fetching has been scheduled
                # We set the expiration date to ROSTER_REFRESH_WINDOW so we'll try again after that period
                request.db.add(
                    TaskDone(
                        key=f"roster::assignment::scheduled::{assignment_id}",
                        data=None,
                        expires_at=datetime.now() + ROSTER_REFRESH_WINDOW,  # noqa: DTZ005
                    )
                )


def schedule_fetching_segment_rosters() -> None:
    """Schedule fetching segment rosters based on their last lunches and the most recent roster fetch."""

    # We use the python version (and not func.now()) for easier mocking during tests
    now = datetime.now()  # noqa: DTZ005

    # Only fetch roster for segments for which we haven't schedule a fetch recently
    no_recent_scheduled_roster_fetch_clause = ~exists(
        select(TaskDone).where(
            TaskDone.key == func.concat("roster::segment::scheduled::", LMSSegment.id),
        )
    )

    # Only fetch roster for segments that don't have recent roster information
    no_recent_roster_clause = ~exists(
        select(LMSSegmentRoster).where(
            LMSSegmentRoster.lms_segment_id == LMSSegment.id,
            LMSSegmentRoster.updated >= now - ROSTER_REFRESH_WINDOW,
        )
    )

    # Only fetch rosters for segments that belong to courses have been recently launched
    recent_launches_clause = exists(
        select(Event)
        .join(Course, Event.course_id == Course.id)
        .where(
            Event.timestamp >= now - LAUNCHED_WINDOW,
            Course.authority_provided_id == LMSCourse.h_authority_provided_id,
        )
    )

    with app.request_context() as request:  # noqa: SIM117
        with request.tm:
            query = (
                select(LMSSegment.id)
                .join(LMSCourse, LMSSegment.lms_course_id == LMSCourse.id)
                .where(
                    # Courses for which we have a LTIA membership service URL
                    LMSCourse.lti_context_memberships_url.is_not(None),
                    no_recent_roster_clause,
                    no_recent_scheduled_roster_fetch_clause,
                    recent_launches_clause,
                    # Only canvas groups for now
                    LMSSegment.type == "canvas_group",
                )
                # Prefer newer segments
                .order_by(LMSSegment.created.desc())
                # Schedule only a few rosters per call to this method
                .limit(ROSTER_LIMIT)
            )
            for lms_segment_id in request.db.scalars(query).all():
                fetch_segment_roster.delay(lms_segment_id=lms_segment_id)
                # Record that the roster fetching has been scheduled
                # We set the expiration date to ROSTER_REFRESH_WINDOW so we'll try again after that period
                request.db.add(
                    TaskDone(
                        key=f"roster::segment::scheduled::{lms_segment_id}",
                        data=None,
                        expires_at=datetime.now() + ROSTER_REFRESH_WINDOW,  # noqa: DTZ005
                    )
                )


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

            # Check the if course has any sections, if it does, schedule fetching its rosters
            if request.db.scalars(
                select(LMSSegment.id).where(
                    LMSSegment.lms_course_id == lms_course_id,
                    LMSSegment.type == "canvas_section",
                )
            ).first():
                fetch_canvas_sections_roster.delay(lms_course_id=lms_course_id)


@app.task(
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=3600,
    retry_backoff_max=7200,
)
def fetch_assignment_roster(*, assignment_id) -> None:
    """Fetch the roster for one assignment."""
    with app.request_context() as request:
        roster_service: RosterService = request.find_service(RosterService)
        with request.tm:
            assignment = request.db.get(Assignment, assignment_id)
            roster_service.fetch_assignment_roster(assignment)


@app.task(
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=3600,
    retry_backoff_max=7200,
)
def fetch_segment_roster(*, lms_segment_id) -> None:
    """Fetch the roster for one segment."""
    with app.request_context() as request:
        roster_service: RosterService = request.find_service(RosterService)
        with request.tm:
            assignment = request.db.get(LMSSegment, lms_segment_id)
            roster_service.fetch_canvas_group_roster(assignment)


@app.task(
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=3600,
    retry_backoff_max=7200,
)
def fetch_canvas_sections_roster(*, lms_course_id) -> None:
    """Fetch the roster for all sections of a given course."""
    with app.request_context() as request:
        roster_service: RosterService = request.find_service(RosterService)
        with request.tm:
            lms_course = request.db.get(LMSCourse, lms_course_id)
            roster_service.fetch_canvas_sections_roster(lms_course)
