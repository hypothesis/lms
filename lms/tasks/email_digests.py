import logging
from datetime import datetime
from typing import List, Optional

from lms.services import DigestService
from lms.tasks.celery import app

LOG = logging.getLogger(__name__)


@app.task
def send_instructor_email_digests(
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
            digest_service.send_instructor_email_digests(
                h_userids,
                updated_after,
                updated_before,
                override_to_email=override_to_email,
            )
