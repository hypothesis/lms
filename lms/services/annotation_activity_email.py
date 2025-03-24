import logging
from dataclasses import asdict

from sqlalchemy import exists, func, select

from lms.models import Assignment, LMSUser, Notification
from lms.services.mailchimp import EmailRecipient, EmailSender
from lms.tasks.mailchimp import send

# Limit for the number of notifications per annotation
ANNOTATION_NOTIFICATION_LIMIT = 100


LOG = logging.getLogger(__name__)


class AnnotationActivityEmailService:
    """Service to send emails for annotation activity (eg. mentions)."""

    def __init__(self, db, sender):
        self._db = db
        self._sender = sender

    def _user_already_notified(self, annotation_id, mentioned_user):
        """Check if a user has already been notified about an annotation."""
        return self._db.execute(
            select(
                exists(Notification).where(
                    Notification.source_annotation_id == annotation_id,
                    Notification.recipient_id == mentioned_user.id,
                )
            )
        ).scalar_one()

    def _over_notification_limit_for_annotation(self, annotation_id):
        """Check if we already sent over ANNOTATION_NOTIFICATION_LIMIT notifications for an annotation."""
        return (
            self._db.execute(
                select(func.count(Notification.id)).where(
                    Notification.source_annotation_id == annotation_id
                )
            ).scalar()
            >= ANNOTATION_NOTIFICATION_LIMIT
        )

    def send_mention(
        self,
        annotation_id: str,
        mentioning_user_h_userid: str,
        mentioned_user_h_userid: str,
        assignment_id: int,
    ) -> Notification | None:
        mentioning_user = self._db.execute(
            select(LMSUser).where(LMSUser.h_userid == mentioning_user_h_userid)
        ).scalar_one()
        mentioned_user = self._db.execute(
            select(LMSUser).where(LMSUser.h_userid == mentioned_user_h_userid)
        ).scalar_one()
        assignment = self._db.execute(
            select(Assignment).where(Assignment.id == assignment_id)
        ).scalar_one()

        if self._user_already_notified(annotation_id, mentioned_user):
            LOG.info(
                "Skipping mention for annotation %r in assignment %r. %r",
                annotation_id,
                assignment_id,
                "user already notified",
            )
            return None

        if self._over_notification_limit_for_annotation(annotation_id):
            LOG.info(
                "Skipping mention for annotation %r in assignment %r. %r",
                annotation_id,
                assignment_id,
                "over annotation limit",
            )
            return None

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

        notification = Notification(
            notification_type=Notification.Type.MENTION,
            source_annotation_id=annotation_id,
            sender_id=mentioning_user.id,
            recipient_id=mentioned_user.id,
            assignment_id=assignment_id,
        )
        self._db.add(notification)
        return notification


def factory(_context, request):
    return AnnotationActivityEmailService(
        db=request.db,
        sender=EmailSender(
            request.registry.settings.get("mailchimp_annotation_activity_subaccount"),
            request.registry.settings.get("mailchimp_annotation_activity_email"),
            request.registry.settings.get("mailchimp_annotation_activity_name"),
        ),
    )
