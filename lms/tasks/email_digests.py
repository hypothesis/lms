import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import Boolean, not_, select

from lms.models import (
    ApplicationInstance,
    AssignmentGrouping,
    AssignmentMembership,
    Event,
    LTIRole,
    TaskDone,
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
def send_instructor_email_digest_tasks():
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
    created_before = datetime(
        year=now.year, month=now.month, day=now.day, hour=5, tzinfo=timezone.utc
    )

    with app.request_context() as request:
        with request.tm:
            candidate_courses = (
                select(Event.course_id)
                .join(ApplicationInstance)
                .where(
                    # Note here that we are considering earlier launches
                    # We rather take a few more courses that miss some cases
                    # where the launch that originated the annotations was made around the cutoff time.
                    Event.timestamp >= created_before - timedelta(days=14),
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
    *, h_userid: str, created_before: str, created_after: str | None = None, **kwargs
) -> None:
    """
    Generate and send instructor email digests to the given users.

    The email digests will cover annotations that were created between the
    `created_after` and `created_before` dates.

    If no `created_after` is given then it defaults to seven days before
    `created_before`.

    Annotations that the user has already been emailed about (according to the
    `task_done` table) won't be covered even if they fall between the
    `created_after` and `created_before` dates.

    :param h_userid: the h_userid of the instructor to email
    :param created_before: cut-off time after which activity will not be
        included in the email, as an ISO 8601 format string
    :param created_after: cut-off time before which activity will not be
        included in the email, as an ISO 8601 format string
    :param kwargs: other keyword arguments to pass to DigestService.send_instructor_email_digest()
    """
    # Caution: datetime.fromisoformat() doesn't support all ISO 8601 strings!
    # This only works for the subset of ISO 8601 produced by datetime.isoformat().
    created_before: datetime = datetime.fromisoformat(created_before)  # type: ignore

    if created_after is None:
        created_after = created_before - timedelta(days=7)  # type: ignore
    else:
        created_after: datetime = datetime.fromisoformat(created_after)  # type: ignore

    with app.request_context() as request:
        with request.tm:
            task_done_data = _get_task_done_data(request.db, h_userid)

            if task_done_data:
                created_after = max(
                    datetime.fromisoformat(task_done_data["created_before"]).replace(
                        tzinfo=timezone.utc
                    ),
                    created_after.replace(tzinfo=timezone.utc),  # type:ignore
                )

            digest_service = request.find_service(DigestService)

            digest_service.send_instructor_email_digest(
                h_userid=h_userid,
                created_after=created_after,
                created_before=created_before,
                **kwargs,
            )


def _get_task_done_data(db_session, h_userid: str) -> dict | None:
    """Return the most recent matching TaskDone.data dict for h_userid."""
    task_dones = db_session.scalars(
        select(TaskDone)
        .where(
            TaskDone.data["type"].as_string() == "instructor_email_digest",
            TaskDone.data["h_userid"].as_string() == h_userid,
            TaskDone.data["created_before"].isnot(None),
        )
        .order_by(TaskDone.data["created_before"].desc())
    )

    for task_done in task_dones:
        try:
            datetime.fromisoformat(task_done.data["created_before"])
        except ValueError:
            continue
        else:
            return task_done.data

    return None
