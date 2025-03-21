from dataclasses import asdict

from sqlalchemy import select

from lms.models import Assignment, LMSUser
from lms.services.mailchimp import EmailRecipient, EmailSender
from lms.tasks.mailchimp import send


class AnnotationActivityEmailService:
    """Service to send emails for annotation activity (eg. mentions)."""

    def __init__(self, db, sender):
        self._db = db
        self._sender = sender

    def send_mention(self, mentioned_user_h_userid, assignment_id: int):
        mentioned_user = self._db.execute(
            select(LMSUser).where(LMSUser.h_userid == mentioned_user_h_userid)
        ).scalar_one()
        assignment = self._db.execute(
            select(Assignment).where(Assignment.id == assignment_id)
        ).scalar_one()

        recipient = EmailRecipient(mentioned_user.email, mentioned_user.display_name)

        email_vars = {
            "assignment_title": assignment.title,
            "course_title": assignment.course.lms_name,
            "mentioned_user": mentioned_user.display_name,
        }
        send.delay(
            template="lms:templates/email/mention/",
            sender=asdict(self._sender),
            recipient=asdict(recipient),
            template_vars=email_vars,
            tags=["lms", "mention"],
        )


def factory(_context, request):
    return AnnotationActivityEmailService(
        db=request.db,
        sender=EmailSender(
            request.registry.settings.get("mailchimp_annotation_activity_subaccount"),
            request.registry.settings.get("mailchimp_annotation_activity_email"),
            request.registry.settings.get("mailchimp_annotation_activity_name"),
        ),
    )
