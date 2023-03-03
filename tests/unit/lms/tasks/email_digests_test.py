from contextlib import contextmanager
from datetime import datetime
from unittest.mock import sentinel

import pytest

from lms.tasks.email_digests import send_instructor_email_digests


@pytest.mark.usefixtures("digest_service")
class TestSendInstructorEmailDigests:
    def test_it(self, digest_service):
        updated_after = datetime(year=2023, month=3, day=1)
        updated_before = datetime(year=2023, month=3, day=2)

        send_instructor_email_digests(
            sentinel.h_userids,
            updated_after.isoformat(),
            updated_before.isoformat(),
            sentinel.override_to_email,
        )

        digest_service.send_instructor_email_digests.assert_called_once_with(
            sentinel.h_userids,
            updated_after,
            updated_before,
            override_to_email=sentinel.override_to_email,
        )

    @pytest.mark.parametrize(
        "updated_after,updated_before",
        [
            ("invalid", "2023-02-28T00:00:00"),
            ("2023-02-28T00:00:00", "invalid"),
            ("invalid", "invalid"),
        ],
    )
    def test_it_crashes_if_updated_after_or_updated_before_is_invalid(
        self, updated_after, updated_before
    ):
        with pytest.raises(ValueError, match="^Invalid isoformat string"):
            send_instructor_email_digests(
                sentinel.h_userids, updated_after, updated_before
            )


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.email_digests.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
