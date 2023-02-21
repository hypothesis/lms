from datetime import datetime, timedelta
from unittest.mock import sentinel, Mock
from contextlib import contextmanager
import pytest

from lms.tasks.email_digests import send_email_digest

pytestmark = pytest.mark.usefixtures("email_digests_service")


class TestSendEmailDigest:
    def test_it(self, email_digests_service, mailchimp_transactional):
        since = datetime(year=2023, month=2, day=14)
        until = since + timedelta(days=1)

        send_email_digest(sentinel.user_id, since.isoformat(), until.isoformat())

        email_digests_service.get.assert_called_once_with(
            sentinel.user_id, since, until
        )
        mailchimp_transactional.Client.assert_called_once_with("TEST_MAILCHIMP_API_KEY")
        mailchimp_transactional.Client.return_value.messages.send_template.assert_called_once_with(
            {
                "template_name": "instructor_email_digest",
                "template_content": [{}],
                "message": {
                    "global_merge_vars": [
                        {"name": "num_annotations", "content": 34},
                        {
                            "name": "courses",
                            "content": [
                                {
                                    "title": "Making sociology fun",
                                    "num_annotations": 30,
                                },
                                {
                                    "title": "History of jazz music",
                                    "num_annotations": 4,
                                },
                            ],
                        },
                    ]
                },
                "async": True,
            }
        )

    @pytest.fixture
    def email_digests_service(self, email_digests_service):
        email_digests_service.get.return_value = {
            "num_annotations": 34,
            "courses": [
                {
                    "title": "Making sociology fun",
                    "num_annotations": 30,
                },
                {
                    "title": "History of jazz music",
                    "num_annotations": 4,
                },
            ],
        }
        return email_digests_service

    @pytest.fixture(autouse=True)
    def mailchimp_transactional(self, patch):
        mailchimp_transactional = patch(
            "lms.tasks.email_digests.mailchimp_transactional"
        )
        mailchimp_transactional.Client.return_value = Mock(spec_set=["messages"])
        return mailchimp_transactional


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    pyramid_request.registry.settings["mailchimp_api_key"] = "TEST_MAILCHIMP_API_KEY"

    app = patch("lms.tasks.email_digests.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
