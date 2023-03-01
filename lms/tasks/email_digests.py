import logging
from datetime import datetime
from typing import List, Optional

from lms.tasks.celery import app

LOG = logging.getLogger(__name__)


@app.task
def send_instructor_email_digests(
    h_userids: List[str],
    since: str,
    until: str,
    override_to_email: Optional[str] = None,
) -> None:
    """
    Generate and send instructor email digests to the given users.

    The email digests will cover activity that occurred in the time period
    described by the `since` and `until` arguments.

    :param h_userids: the h_userid's of the instructors to email
    :param since: the beginning of the time period as an ISO 8601 format string
    :param until: the end of the time period as an ISO 8601 format string

    :param override_to_email: send all the emails to this email address instead
        of the users' email addresses (this is for test purposes)
    """
    # Caution: datetime.fromisoformat() doesn't support all ISO 8601 strings!
    # This only works for the subset of ISO 8601 produced by datetime.isoformat().
    since = datetime.fromisoformat(since)
    until = datetime.fromisoformat(until)

    with app.request_context() as request:  # pylint:disable=no-member
        with request.tm:
            LOG.info(
                "send_instructor_email_digests(%r, %r, %r, override_to_email=%r)",
                h_userids,
                since,
                until,
                override_to_email,
            )
