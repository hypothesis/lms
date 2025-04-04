import logging
from dataclasses import asdict

from sqlalchemy import exists, func, select

from lms.models import Assignment, LMSUser, Notification
from lms.services.email_preferences import EmailPreferencesService, EmailTypes
from lms.services.mailchimp import EmailRecipient, EmailSender
from lms.tasks.mailchimp import send

# Limit for the number of notifications per annotation
ANNOTATION_NOTIFICATION_LIMIT = 100


LOG = logging.getLogger(__name__)


class AnnotationActivityEmailService:
    """Service to send emails for annotation activity (eg. mentions)."""

    def __init__(self, db, sender, email_preferences_service: EmailPreferencesService):
        self._db = db
        self._sender = sender
        self._email_preferences_service = email_preferences_service

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

    def send_mention(  # noqa: PLR0913
        self,
        annotation_id: str,
        annotation_text: str,
        annotation_quote: str | None,
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

        email_preferences = self._email_preferences_service.get_preferences(
            mentioned_user.h_userid
        )

        if not email_preferences.mention_email_feature_enabled:
            self._log_skip_notification(
                annotation_id, assignment_id, "feature disabled"
            )
            return None

        if not email_preferences.mention_email_subscribed:
            self._log_skip_notification(
                annotation_id, assignment_id, "user unsubscribed"
            )
            return None

        if self._user_already_notified(annotation_id, mentioned_user):
            self._log_skip_notification(
                annotation_id, assignment_id, "user already notified"
            )
            return None

        if self._over_notification_limit_for_annotation(annotation_id):
            self._log_skip_notification(
                annotation_id, assignment_id, "over annotation limit"
            )
            return None

        recipient = EmailRecipient(mentioned_user.email, mentioned_user.display_name)
        email_vars = {
            "assignment_title": assignment.title,
            "course_title": assignment.course.lms_name,
            "annotation_text": annotation_text,
            "annotation_quote": annotation_quote,
            "preferences_url": self._email_preferences_service.preferences_url(
                mentioned_user.h_userid, EmailTypes.MENTION
            ),
        }
        send.delay(
            template="lms:templates/email/mention/",
            sender=asdict(self._sender),
            recipient=asdict(recipient),
            template_vars=email_vars,
            tags=["lms", "mention"],
            unsubscribe_url=self._email_preferences_service.unsubscribe_url(
                mentioned_user.h_userid, EmailTypes.MENTION
            ),
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

    def _log_skip_notification(self, annotation_id, assignment_id, reason):
        LOG.info(
            "Skipping mention for annotation %r in assignment %r. %r",
            annotation_id,
            assignment_id,
            reason,
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
