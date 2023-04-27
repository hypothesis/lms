from contextlib import contextmanager
from dataclasses import asdict
from unittest.mock import sentinel

import pytest

from lms.services.mailchimp import EmailRecipient, EmailSender
from lms.tasks.mailchimp import send_template


@pytest.mark.usefixtures("mailchimp_service")
class TestSendTemplate:
    def test_it(self, mailchimp_service):
        sender = EmailSender("subaccount", "sender_email", "sender_name")
        recipient = EmailRecipient("recipient_email", "recipient_name")

        send_template(
            sender=asdict(sender),
            recipient=asdict(recipient),
            template_name=sentinel.template_name,
            template_vars=sentinel.template_vars,
        )

        mailchimp_service.send_template.assert_called_once_with(
            sender=sender,
            recipient=recipient,
            template_name=sentinel.template_name,
            template_vars=sentinel.template_vars,
        )


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.mailchimp.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
