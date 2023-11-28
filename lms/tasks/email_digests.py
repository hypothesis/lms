import logging
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import select

from lms.models import (
    ApplicationInstance,
    AssignmentGrouping,
    AssignmentMembership,
    Event,
    LTIRole,
    User
)
from lms.services import DigestService
from lms.tasks.celery import app

LOG = logging.getLogger(__name__)


@app.task(
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=3600,
    retry_backoff_max=7200,
)
def send_instructor_email_digest_tasks(*, batch_size):
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
                .where(
                    # Consider only assignments that belong to the candidate courses selected before
                    AssignmentGrouping.grouping_id.in_(
                        select(candidate_courses.c.course_id)
                    ),
                    LTIRole.type == "instructor",
                )
            ).all()

            batches = [
                h_userids[i : i + batch_size]
                for i in range(0, len(h_userids), batch_size)
            ]

            for batch in batches:
                send_instructor_email_digests.apply_async(
                    (),
                    {
                        "h_userids": batch,
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
def send_instructor_email_digests(
    *, h_userids: List[str], created_after: str, created_before: str, **kwargs
) -> None:
    """
    Generate and send instructor email digests to the given users.

    The email digests will cover activity that occurred in the time period
    described by the `created_after` and `created_before` arguments.

    :param h_userids: the h_userid's of the instructors to email
    :param created_after: the beginning of the time period as an ISO 8601 format string
    :param created_before: the end of the time period as an ISO 8601 format string
    :param kwargs: other keyword arguments to pass to DigestService.send_instructor_email_digests()
    """
    # Caution: datetime.fromisoformat() doesn't support all ISO 8601 strings!
    # This only works for the subset of ISO 8601 produced by datetime.isoformat().
    created_after = datetime.fromisoformat(created_after)
    created_before = datetime.fromisoformat(created_before)

    with app.request_context() as request:  # pylint:disable=no-member
        with request.tm:
            digest_service = request.find_service(DigestService)

            digest_service.send_instructor_email_digests(
                h_userids, created_after, created_before, **kwargs
            )
