"""Celery tasks for sending emails using Mailchimp."""

from lms.services.mailchimp import EmailRecipient, EmailSender
from lms.tasks.celery import app


@app.task(
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=3600,
    retry_backoff_max=7200,
)
def send(*, sender, recipient, **kwargs) -> None:
    """Send an email using Mailchimp's API."""

    sender = EmailSender(**sender)
    recipient = EmailRecipient(**recipient)

    with app.request_context() as request:  # pylint:disable=no-member
        mailchimp_service = request.find_service(name="mailchimp")
        print(request.environ)
        with request.tm:
            mailchimp_service.send(sender=sender, recipient=recipient, **kwargs)


@app.task(
    acks_late=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=3600,
    retry_backoff_max=7200,
)
def send_template(*, sender, recipient, **kwargs) -> None:
    """Send an email using Mailchimp's send-template API."""

    sender = EmailSender(**sender)
    recipient = EmailRecipient(**recipient)

    with app.request_context() as request:  # pylint:disable=no-member
        mailchimp_service = request.find_service(name="mailchimp")
        with request.tm:
            mailchimp_service.send_template(
                sender=sender, recipient=recipient, **kwargs
            )
