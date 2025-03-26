from dataclasses import asdict

from sqlalchemy import select

from lms.models import Assignment, LMSUser, Notification
from lms.services.email_preferences import EmailPreferencesService
from lms.services.mailchimp import EmailRecipient, EmailSender
from lms.tasks.mailchimp import send


class AnnotationActivityEmailService:
    """Service to send emails for annotation activity (eg. mentions)."""

    def __init__(self, db, sender, email_preferences_service: EmailPreferencesService):
        self._db = db
        self._sender = sender
        self._email_preferences_service = email_preferences_service

    def send_mention(
        self,
        annotation_id: str,
        annotation_text: str,
        mentioning_user_h_userid: str,
        mentioned_user_h_userid: str,
        assignment_id: int,
    ):
        mentioning_user = self._db.execute(
            select(LMSUser).where(LMSUser.h_userid == mentioning_user_h_userid)
        ).scalar_one()

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
            "annotation_text": annotation_text,
            "preferences_url": self._email_preferences_service.preferences_url(
                mentioned_user.h_userid, "mention"
            ),
        }
        send.delay(
            template="lms:templates/email/mention/",
            sender=asdict(self._sender),
            recipient=asdict(recipient),
            template_vars=email_vars,
            tags=["lms", "mention"],
            unsubscribe_url=self._email_preferences_service.unsubscribe_url(
                mentioned_user.h_userid, "mention"
            ),
        )
        self._db.add(
            Notification(
                notification_type=Notification.Type.MENTION,
                source_annotation_id=annotation_id,
                sender_id=mentioning_user.id,
                recipient_id=mentioned_user.id,
                assignment_id=assignment_id,
            )
        )


def factory(_context, request):
    return AnnotationActivityEmailService(
        db=request.db,
        sender=EmailSender(
            request.registry.settings.get("mailchimp_annotation_activity_subaccount"),
            request.registry.settings.get("mailchimp_annotation_activity_email"),
            request.registry.settings.get("mailchimp_annotation_activity_name"),
        ),
        email_preferences_service=request.find_service(EmailPreferencesService),
    )
