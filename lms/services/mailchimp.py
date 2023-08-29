import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import mailchimp_transactional
from pyramid.renderers import render
from sqlalchemy import select

from lms.models import TaskDone

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


class MailchimpError(Exception):
    """An error when sending an email."""


class MailchimpService:
    def __init__(self, db, api_key):
        self.db = db
        self.mailchimp_client = mailchimp_transactional.Client(api_key)

    def send(  # pylint:disable=too-many-arguments
        self,
        template: str,
        sender: EmailSender,
        recipient: EmailRecipient,
        template_vars: dict,
        unsubscribe_url: Optional[str] = None,
        task_done_key: Optional[str] = None,
    ):
        """
        Send an email using Mailchimp Transactional's API.

        https://mailchimp.com/developer/transactional/api/messages/send-new-message/
        """

        if task_done_key:
            if self.db.execute(
                select(TaskDone).filter_by(key=task_done_key)
            ).one_or_none():
                LOG.info("Not sending duplicate email %s", task_done_key)
                return

        headers = {}

        if unsubscribe_url:
            template_vars["unsubscribe_url"] = unsubscribe_url
            headers["List-Unsubscribe"] = unsubscribe_url

        subject = render(str(template / Path("subject.jinja2")), template_vars)

        params = {
            "message": {
                "subject": subject,
                "html": "...",  # For logging only, will be replaced below.
                "subaccount": sender.subaccount,
                "from_email": sender.email,
                "from_name": sender.name,
                "to": [{"email": recipient.email, "name": recipient.name}],
                "track_opens": True,
                "track_clicks": True,
                "auto_text": True,
                "headers": headers,
            },
            "async": True,
        }

        LOG.info("mailchimp_client.send(%r)", params)

        # The HTML body might be long so add it to the params *after* logging.
        params["message"]["html"] = render(
            str(template / Path("body.html.jinja2")), template_vars
        )

        try:
            self.mailchimp_client.messages.send(params)
        except Exception as exc:
            raise MailchimpError() from exc

        if task_done_key:
            # Record the email send in the DB to avoid sending duplicates.
            self.db.add(TaskDone(key=task_done_key))

    def send_template(  # pylint:disable=too-many-arguments
        self,
        template_name: str,
        sender: EmailSender,
        recipient: EmailRecipient,
        template_vars: dict,
        unsubscribe_url: Optional[str] = None,
        task_done_key: Optional[str] = None,
    ):
        """
        Send an email using Mailchimp Transactional's send-template API.

        https://mailchimp.com/developer/transactional/api/messages/send-using-message-template/
        """

        if task_done_key:
            if self.db.execute(
                select(TaskDone).filter_by(key=task_done_key)
            ).one_or_none():
                LOG.info("Not sending duplicate email %s", task_done_key)
                return

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

        try:
            self.mailchimp_client.messages.send_template(params)
        except Exception as exc:
            raise MailchimpError() from exc

        if task_done_key:
            # Record the email send in the DB to avoid sending duplicates.
            self.db.add(TaskDone(key=task_done_key))


def factory(_context, request):
    return MailchimpService(request.db, request.registry.settings["mailchimp_api_key"])
