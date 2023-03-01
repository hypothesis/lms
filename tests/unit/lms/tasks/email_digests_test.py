import logging
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import sentinel

import pytest

from lms.tasks.email_digests import send_instructor_email_digests


class TestSendInstructorEmailDigests:
    def test_it(self, caplog):
        caplog.set_level(logging.INFO)
        since = datetime(year=2023, month=3, day=1)
        until = datetime(year=2023, month=3, day=2)

        send_instructor_email_digests(
            sentinel.h_userids,
            since.isoformat(),
            until.isoformat(),
            sentinel.override_to_email,
        )

        assert caplog.record_tuples == [
            (
                "lms.tasks.email_digests",
                logging.INFO,
                "send_instructor_email_digests(sentinel.h_userids, datetime.datetime(2023, 3, 1, 0, 0), datetime.datetime(2023, 3, 2, 0, 0), override_to_email=sentinel.override_to_email)",
            )
        ]

    @pytest.mark.parametrize(
        "since,until",
        [
            ("invalid", "2023-02-28T00:00:00"),
            ("2023-02-28T00:00:00", "invalid"),
            ("invalid", "invalid"),
        ],
    )
    def test_it_crashes_if_since_or_until_is_invalid(self, since, until):
        with pytest.raises(ValueError, match="^Invalid isoformat string"):
            send_instructor_email_digests(sentinel.h_userids, since, until)


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.email_digests.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
