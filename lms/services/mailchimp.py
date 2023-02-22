import logging
from dataclasses import dataclass
from typing import List

import mailchimp_transactional

from lms.services.digest import InstructorDigests

LOG = logging.getLogger(__name__)


@dataclass
class EmailSender:
    subaccount: str
    """The Mailchimp subaccount ID to use to send the email."""

    email: str
    """The email address that the email will appear to come from."""

    name: str
    """The full name that the email will appear to come from."""


@dataclass
class EmailRecipient:
    email: str
    """The email address to send to."""

    name: str
    """The recipient full name to use in the email's To: header."""


class MailchimpService:
    def __init__(self, api_key, digests_sender):
        self.api_key = api_key
        self.digests_sender = digests_sender

    def send_template(
        self,
        template_name: str,
        sender: EmailSender,
        recipient: EmailRecipient,
        merge_vars: List[dict],
    ):
        """
        Send an email using Mailchimp Transactional's send-template API.

        https://mailchimp.com/developer/transactional/api/messages/send-using-message-template/
        """
        params = {
            "template_name": template_name,
            "message": {
                "subaccount": sender.subaccount,
                "from_email": sender.email,
                "from_name": sender.name,
                "to": [{"email": recipient.email, "name": recipient.name}],
                "track_opens": True,
                "track_clicks": True,
                "global_merge_vars": merge_vars,
            },
            "async": True,
        }

        if self.api_key:
            mailchimp_client = mailchimp_transactional.Client(self.api_key)
            mailchimp_client.messages.send_template(params)
        else:
            LOG.info(params)

    def send_instructor_digests(self, digests: InstructorDigests):
        """Send the given instructor digests as emails."""

        for digest in digests.values():
            courses = []

            for course_digest in digest.courses.values():
                courses.append(
                    {
                        "title": course_digest.course.title,
                        "num_annotations": sum(
                            len(annotations)
                            for annotations in course_digest.users.values()
                        ),
                    }
                )

            self.send_template(
                "instructor_digest",
                self.digests_sender,
                EmailRecipient(
                    digest.user.email,
                    digest.user.name,
                ),
                merge_vars=[
                    {
                        "name": "num_annotations",
                        "content": sum(course["num_annotations"] for course in courses),
                    },
                    {"name": "courses", "content": courses},
                ],
            )


def factory(_context, request):
    return MailchimpService(
        request.registry.settings.get("mailchimp_api_key"),
        digests_sender=EmailSender(
            request.registry.settings.get("mailchimp_digests_subaccount"),
            request.registry.settings.get("mailchimp_digests_email"),
            request.registry.settings.get("mailchimp_digests_name"),
        ),
    )
