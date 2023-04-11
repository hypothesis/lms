import logging
from dataclasses import dataclass
from typing import Optional

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

    def send_template(  # pylint:disable=too-many-arguments
        self,
        template_name: str,
        sender: EmailSender,
        recipient: EmailRecipient,
        template_vars: dict,
        unsubscribe_url: Optional[str] = None,
    ):
        """
        Send an email using Mailchimp Transactional's send-template API.

        https://mailchimp.com/developer/transactional/api/messages/send-using-message-template/
        """
        headers = {}

        if unsubscribe_url:
            # If we do provide a unsubscribe_url expose it as template var
            # and add the corresponding header for clients that support it.
            template_vars["unsubscribe_url"] = unsubscribe_url
            headers["List-Unsubscribe"] = unsubscribe_url

        params = {
            "template_name": template_name,
            # We're not using template_content but we still need to pass an
            # empty value or the Mailchimp API call fails.
            "template_content": [{}],
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
                "headers": headers,
            },
            "async": True,
        }

        LOG.info("mailchimp_client.send_template(%r)", params)

        if hasattr(self, "mailchimp_client"):
            self.mailchimp_client.messages.send_template(params)


def factory(_context, request):
    return MailchimpService(request.registry.settings.get("mailchimp_api_key"))
