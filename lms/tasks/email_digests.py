import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, not_, select

from lms.models import (
    ApplicationInstance,
    AssignmentGrouping,
    AssignmentMembership,
    Event,
    LTIRole,
    User,
    UserPreferences,
)
from lms.services import DigestService, EmailPreferencesService, EmailPrefs
from lms.tasks.celery import app

LOG = logging.getLogger(__name__)


@app.task(
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=3600,
    retry_backoff_max=7200,
)
def send_instructor_email_digest_tasks(*, batch_size):  # pylint:disable=unused-argument
    """
    Generate and send instructor email digests.

    The email digests will cover activity that occurred in the time period from
    5AM UTC yesterday morning to 5AM UTC this morning.

    Emails will be sent to all instructors who're participating in the feature
    and who have digest activity in the time period.

    5AM UTC is chosen because it equates to midnight EST. Most of our target
    users for this feature are in the EST timezone and we want each email
    digests to cover "yesterday" (midnight to midnight) EST.

    EST is 5 hours behind UTC (ignoring daylight savings for simplicity: we
    don't need complete accuracy in the timing).
    """
    now = datetime.now(timezone.utc)
    weekday = EmailPrefs.DAYS[now.weekday()]
    created_before = datetime(year=now.year, month=now.month, day=now.day, hour=5)
    created_after = created_before - timedelta(days=1)

    with app.request_context() as request:  # pylint:disable=no-member
        with request.tm:
            candidate_courses = (
                select(Event.course_id)
                .join(ApplicationInstance)
                .where(
                    # Note here that we are considering earlier launches
                    # We rather take a few more courses that miss some cases
                    # where the launch that originated the annotations was made around the cutoff time.
                    Event.timestamp >= created_after - timedelta(days=7),
                    Event.timestamp <= created_before,
                    # Only courses that belong to AIs with the feature enabled
                    ApplicationInstance.settings["hypothesis"][
                        "instructor_email_digests_enabled"
                    ].astext
                    == "true",
                )
            ).cte("candidate_courses")

            h_userids = request.db.scalars(
                select(User.h_userid)
                .select_from(User)
                .distinct()
                # Although we don't care about assignments we use the assignment based tables
                # as they have the correct LTIRole information.
                # GroupingMembership doesn't role information at all
                # and the User.roles information can't be trusted
                # (only reflects the last role we've seen, in any course)
                .join(AssignmentMembership)
                .join(
                    AssignmentGrouping,
                    AssignmentGrouping.assignment_id
                    == AssignmentMembership.assignment_id,
                )
                .join(LTIRole)
                .outerjoin(UserPreferences, User.h_userid == UserPreferences.h_userid)
                .where(
                    # Consider only assignments that belong to the candidate courses selected before
                    AssignmentGrouping.grouping_id.in_(
                        select(candidate_courses.c.course_id)
                    ),
                    LTIRole.type == "instructor",
                    not_(
                        UserPreferences.preferences[
                            f"{EmailPreferencesService.KEY_PREFIX}{weekday}"
                        ]
                        .astext.cast(Boolean)
                        .is_(False)
                    ),
                )
            ).all()

            for h_userid in h_userids:
                send_instructor_email_digest.apply_async(
                    (),
                    {
                        "h_userid": h_userid,
                        "created_after": created_after.isoformat(),
                        "created_before": created_before.isoformat(),
                    },
                )


@app.task(
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=3600,
    retry_backoff_max=7200,
    rate_limit="10/m",
)
def send_instructor_email_digest(
    *, h_userid: str, created_after: str, created_before: str, **kwargs
) -> None:
    """
    Generate and send instructor email digests to the given users.

    The email digests will cover activity that occurred in the time period
    described by the `created_after` and `created_before` arguments.

    :param h_userid: the h_userid of the instructor to email
    :param created_after: the beginning of the time period as an ISO 8601 format string
    :param created_before: the end of the time period as an ISO 8601 format string
    :param kwargs: other keyword arguments to pass to DigestService.send_instructor_email_digest()
    """
    # Caution: datetime.fromisoformat() doesn't support all ISO 8601 strings!
    # This only works for the subset of ISO 8601 produced by datetime.isoformat().
    created_after = datetime.fromisoformat(created_after)
    created_before = datetime.fromisoformat(created_before)

    with app.request_context() as request:  # pylint:disable=no-member
        with request.tm:
            digest_service = request.find_service(DigestService)

            digest_service.send_instructor_email_digest(
                h_userid, created_after, created_before, **kwargs
            )
