from dataclasses import asdict
from unittest.mock import sentinel

import pytest

from lms.services.annotation_activity_email import (
    AnnotationActivityEmailService,
    factory,
)
from lms.services.mailchimp import EmailRecipient, EmailSender
from tests import factories


class TestAnnotationActivityEmailService:
    def test_send_mention(
        self, svc, mentioned_user, assignment, db_session, send, sender
    ):
        db_session.flush()

        svc.send_mention(mentioned_user.h_userid, assignment.id)

        send.delay.assert_called_once_with(
            template="lms:templates/email/mention/",
            sender=asdict(sender),
            recipient=asdict(
                EmailRecipient(mentioned_user.email, mentioned_user.display_name)
            ),
            template_vars={
                "assignment_title": assignment.title,
                "course_title": assignment.course.lms_name,
                "mentioned_user": mentioned_user.display_name,
            },
            tags=["lms", "mention"],
        )

    @pytest.fixture
    def mentioned_user(self):
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
    def svc(self, db_session, sender):
        return AnnotationActivityEmailService(db_session, sender)


class TestServiceFactory:
    def test_it(self, pyramid_request, AnnotationActivityEmailService):
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
        )
        assert service == AnnotationActivityEmailService.return_value

    @pytest.fixture
    def AnnotationActivityEmailService(self, patch):
        return patch(
            "lms.services.annotation_activity_email.AnnotationActivityEmailService"
        )
