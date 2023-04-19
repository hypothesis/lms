import logging
import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from h_pyramid_sentry import report_exception
from sqlalchemy import and_, select

from lms.models import (
    ApplicationInstance,
    AssignmentMembership,
    EmailUnsubscribe,
    LTIRole,
    User,
)
from lms.services import DigestService
from lms.services.digest import SendDigestsError
from lms.tasks.celery import app

LOG = logging.getLogger(__name__)


@app.task(acks_late=True, bind=True, max_retries=2)
def send_instructor_email_digest_tasks(self, *, batch_size, h_userids=None):
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
            if not h_userids:
                try:
                    h_userids = request.db.scalars(
                        select(User.h_userid)
                        .select_from(User)
                        .distinct()
                        .join(ApplicationInstance)
                        .join(AssignmentMembership)
                        .join(LTIRole)
                        .outerjoin(
                            EmailUnsubscribe,
                            and_(
                                User.h_userid == EmailUnsubscribe.h_userid,
                                EmailUnsubscribe.tag
                                == EmailUnsubscribe.Tag.INSTRUCTOR_DIGEST,
                            ),
                        )
                        .where(
                            ApplicationInstance.settings["hypothesis"][
                                "instructor_email_digests_enabled"
                            ].astext
                            == "true",
                            LTIRole.type == "instructor",
                            # No EmailUnsubscribes
                            EmailUnsubscribe.id.is_(None),
                        )
                    ).all()
                except Exception as exc:  # pylint:disable=broad-exception-caught
                    LOG.exception(exc)
                    report_exception(exc)
                    self.retry(countdown=_retry_countdown(self.request))

            batches = [
                h_userids[i : i + batch_size]
                for i in range(0, len(h_userids), batch_size)
            ]

            failed_h_userids = []

            for batch in batches:
                try:
                    send_instructor_email_digests.apply_async(
                        (),
                        {
                            "h_userids": batch,
                            "updated_after": updated_after,
                            "updated_before": updated_before,
                        },
                    )
                except Exception as exc:  # pylint:disable=broad-exception-caught
                    LOG.exception(exc)
                    report_exception(exc)
                    failed_h_userids.extend(batch)

            if failed_h_userids:
                self.retry(
                    kwargs={
                        **self.request.kwargs,
                        "h_userids": failed_h_userids,
                    },
                    countdown=_retry_countdown(self.request),
                )


@app.task(acks_late=True, bind=True, max_retries=2)
def send_instructor_email_digests(
    self,
    *,
    h_userids: List[str],
    updated_after: str,
    updated_before: str,
    override_to_email: Optional[str] = None,
) -> None:
    """
    Generate and send instructor email digests to the given users.

    The email digests will cover activity that occurred in the time period
    described by the `updated_after` and `updated_before` arguments.

    :param h_userids: the h_userid's of the instructors to email
    :param updated_after: the beginning of the time period as an ISO 8601 format string
    :param updated_before: the end of the time period as an ISO 8601 format string

    :param override_to_email: send all the emails to this email address instead
        of the users' email addresses (this is for test purposes)
    """
    # Caution: datetime.fromisoformat() doesn't support all ISO 8601 strings!
    # This only works for the subset of ISO 8601 produced by datetime.isoformat().
    updated_after = datetime.fromisoformat(updated_after)
    updated_before = datetime.fromisoformat(updated_before)

    with app.request_context() as request:  # pylint:disable=no-member
        with request.tm:
            digest_service = request.find_service(DigestService)

            try:
                digest_service.send_instructor_email_digests(
                    h_userids,
                    updated_after,
                    updated_before,
                    override_to_email=override_to_email,
                )
            except SendDigestsError as err:
                self.retry(
                    kwargs={
                        **self.request.kwargs,
                        "h_userids": list(err.errors.keys()),
                    },
                    countdown=_retry_countdown(self.request),
                )
            except Exception as exc:  # pylint:disable=broad-exception-caught
                LOG.exception(exc)
                report_exception(exc)
                self.retry(countdown=_retry_countdown(self.request))


def _retry_countdown(celery_request):
    return (3600 * (celery_request.retries + 1)) + random.randint(0, 900)
