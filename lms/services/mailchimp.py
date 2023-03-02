import logging
from dataclasses import dataclass

import mailchimp_transactional

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
    def __init__(self, api_key):
        if api_key:
            self.mailchimp_client = mailchimp_transactional.Client(api_key)

    def send_template(
        self,
        template_name: str,
        sender: EmailSender,
        recipient: EmailRecipient,
        template_vars: dict,
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
                "global_merge_vars": [
                    {"name": key, "content": value}
                    for key, value in template_vars.items()
                ],
            },
            "async": True,
        }

        if hasattr(self, "mailchimp_client"):
            self.mailchimp_client.messages.send_template(params)
        else:
            LOG.info(params)


def factory(_context, request):
    return MailchimpService(request.registry.settings.get("mailchimp_api_key"))
