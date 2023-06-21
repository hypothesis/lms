import logging
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import select

from lms.models import (
    ApplicationInstance,
    AssignmentMembership,
    EmailUnsubscribe,
    LTIRole,
    User,
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
    updated_before = datetime(year=now.year, month=now.month, day=now.day, hour=5)
    updated_after = updated_before - timedelta(days=1)
    updated_before = updated_before.isoformat()
    updated_after = updated_after.isoformat()

    with app.request_context() as request:  # pylint:disable=no-member
        with request.tm:
            h_userids = request.db.scalars(
                select(User.h_userid)
                .select_from(User)
                .distinct()
                .join(ApplicationInstance)
                .join(AssignmentMembership)
                .join(LTIRole)
                .where(
                    ApplicationInstance.settings["hypothesis"][
                        "instructor_email_digests_enabled"
                    ].astext
                    == "true",
                    LTIRole.type == "instructor",
                    # No EmailUnsubscribes
                    User.h_userid.not_in(
                        select(EmailUnsubscribe.h_userid).where(
                            EmailUnsubscribe.tag
                            == EmailUnsubscribe.Tag.INSTRUCTOR_DIGEST
                        )
                    ),
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
                        "updated_after": updated_after,
                        "updated_before": updated_before,
                    },
                )


@app.task(
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=3600,
    retry_backoff_max=7200,
    rate_limit="1/m",
)
def send_instructor_email_digests(
    *, h_userids: List[str], updated_after: str, updated_before: str, **kwargs
) -> None:
    """
    Generate and send instructor email digests to the given users.

    The email digests will cover activity that occurred in the time period
    described by the `updated_after` and `updated_before` arguments.

    :param h_userids: the h_userid's of the instructors to email
    :param updated_after: the beginning of the time period as an ISO 8601 format string
    :param updated_before: the end of the time period as an ISO 8601 format string
    :param kwargs: other keyword arguments to pass to DigestService.send_instructor_email_digests()
    """
    # Caution: datetime.fromisoformat() doesn't support all ISO 8601 strings!
    # This only works for the subset of ISO 8601 produced by datetime.isoformat().
    updated_after = datetime.fromisoformat(updated_after)
    updated_before = datetime.fromisoformat(updated_before)

    with app.request_context() as request:  # pylint:disable=no-member
        with request.tm:
            digest_service = request.find_service(DigestService)

            digest_service.send_instructor_email_digests(
                h_userids, updated_after, updated_before, **kwargs
            )
