from dataclasses import asdict
from unittest.mock import sentinel

import pytest
from sqlalchemy import select

from lms.models import Notification
from lms.services.annotation_activity_email import (
    ANNOTATION_NOTIFICATION_LIMIT,
    AnnotationActivityEmailService,
    factory,
)
from lms.services.mailchimp import EmailRecipient, EmailSender
from tests import factories


class TestAnnotationActivityEmailService:
    def test_send_mention(
        self,
        svc,
        mentioning_user,
        mentioned_user,
        assignment,
        db_session,
        send,
        sender,
        email_preferences_service,
    ):
        db_session.flush()

        svc.send_mention(
            "ANNOTATION_ID",
            "ANNOTATION_TEXT",
            "ANNOTATION_QUOTE",
            mentioning_user.h_userid,
            mentioned_user.h_userid,
            assignment.id,
        )

        email_preferences_service.unsubscribe_url.assert_called_once_with(
            mentioned_user.h_userid, "mention"
        )
        email_preferences_service.preferences_url.assert_called_once_with(
            mentioned_user.h_userid, "mention"
        )
        send.delay.assert_called_once_with(
            template="lms:templates/email/mention/",
            sender=asdict(sender),
            recipient=asdict(
                EmailRecipient(mentioned_user.email, mentioned_user.display_name)
            ),
            template_vars={
                "assignment_title": assignment.title,
                "annotation_text": "ANNOTATION_TEXT",
                "annotation_quote": "ANNOTATION_QUOTE",
                "course_title": assignment.course.lms_name,
                "preferences_url": email_preferences_service.preferences_url.return_value,
            },
            tags=["lms", "mention"],
            unsubscribe_url=email_preferences_service.unsubscribe_url.return_value,
        )

        notification = db_session.execute(select(Notification)).scalar_one()
        assert notification.notification_type == Notification.Type.MENTION
        assert notification.source_annotation_id == "ANNOTATION_ID"
        assert notification.sender_id == mentioning_user.id
        assert notification.recipient_id == mentioned_user.id
        assert notification.assignment_id == assignment.id

    @pytest.mark.parametrize(
        "fixture_name",
        ["notification_for_mentioned_user", "notifications_for_annotation"],
    )
    def test_with_should_not_notify(
        self,
        fixture_name,
        request,
        svc,
        send,
        db_session,
        mentioning_user,
        mentioned_user,
        assignment,
    ):
        _ = request.getfixturevalue(fixture_name)
        db_session.flush()

        assert not svc.send_mention(
            "ANNOTATION_ID",
            "ANNOTATION_TEXT",
            "ANNOTATION_QUOTE",
            mentioning_user.h_userid,
            mentioned_user.h_userid,
            assignment.id,
        )

        send.delay.assert_not_called()

    @pytest.fixture
    def notification_for_mentioned_user(
        self, mentioned_user, mentioning_user, assignment
    ):
        return factories.Notification(
            source_annotation_id="ANNOTATION_ID",
            recipient=mentioned_user,
            sender=mentioning_user,
            assignment=assignment,
            notification_type=Notification.Type.MENTION,
        )

    @pytest.fixture
    def notifications_for_annotation(self, assignment):
        for _ in range(ANNOTATION_NOTIFICATION_LIMIT):
            factories.Notification(
                source_annotation_id="ANNOTATION_ID",
                recipient=factories.LMSUser(),
                sender=factories.LMSUser(),
                assignment=assignment,
                notification_type=Notification.Type.MENTION,
            )

    @pytest.fixture
    def mentioned_user(self):
        return factories.LMSUser()

    @pytest.fixture
    def mentioning_user(self):
        return factories.LMSUser()

    @pytest.fixture
    def assignment(self):
        return factories.Assignment(course=factories.Course())

    @pytest.fixture
    def send(self, patch):
        return patch("lms.services.annotation_activity_email.send")

    @pytest.fixture
    def sender(self):
        return EmailSender(
            sentinel.annotation_activity_subaccount,
            sentinel.annotation_activity_from_email,
            sentinel.annotation_activity_from_name,
        )

    @pytest.fixture
    def svc(self, db_session, sender, email_preferences_service):
        return AnnotationActivityEmailService(
            db_session, sender, email_preferences_service=email_preferences_service
        )


class TestServiceFactory:
    def test_it(
        self, pyramid_request, AnnotationActivityEmailService, email_preferences_service
    ):
        settings = pyramid_request.registry.settings
        settings["mailchimp_annotation_activity_subaccount"] = (
            sentinel.annotation_activity_subaccount
        )
        settings["mailchimp_annotation_activity_email"] = (
            sentinel.annotation_activity_from_email
        )
        settings["mailchimp_annotation_activity_name"] = (
            sentinel.annotation_activity_from_name
        )

        service = factory(sentinel.context, pyramid_request)

        AnnotationActivityEmailService.assert_called_once_with(
            db=pyramid_request.db,
            sender=EmailSender(
                sentinel.annotation_activity_subaccount,
                sentinel.annotation_activity_from_email,
                sentinel.annotation_activity_from_name,
            ),
            email_preferences_service=email_preferences_service,
        )
        assert service == AnnotationActivityEmailService.return_value

    @pytest.fixture
    def AnnotationActivityEmailService(self, patch):
        return patch(
            "lms.services.annotation_activity_email.AnnotationActivityEmailService"
        )
