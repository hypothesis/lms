from unittest.mock import call, sentinel

import factory
import pytest

from lms.services.digest._digest_context import UnifiedUser
from lms.services.digest.service import DigestService
from lms.services.mailchimp import EmailRecipient, EmailSender
from tests import factories


class TestDigestService:
    def test_send_instructor_email_digests(
        self, svc, h_api, context, DigestContext, db_session, mailchimp_service, sender
    ):
        audience = ["userid1", "userid2"]
        context.unified_users = {
            "userid1": UnifiedUserFactory(h_userid="userid1"),
            "userid2": UnifiedUserFactory(h_userid="userid2"),
        }
        digests = context.instructor_digest.side_effect = [
            {"total_annotations": 1},
            {"total_annotations": 2},
        ]

        svc.send_instructor_email_digests(
            audience, sentinel.updated_after, sentinel.updated_before
        )

        h_api.get_annotations.assert_called_once_with(
            audience, sentinel.updated_after, sentinel.updated_before
        )
        DigestContext.assert_called_once_with(
            db_session, audience, h_api.get_annotations.return_value
        )
        assert context.instructor_digest.call_args_list == [
            call(h_userid) for h_userid in audience
        ]
        assert mailchimp_service.send_template.call_args_list == [
            call(
                "instructor-email-digest",
                sender,
                recipient=EmailRecipient(unified_user.email, unified_user.display_name),
                template_vars=digest,
            )
            for unified_user, digest in zip(context.unified_users.values(), digests)
        ]

    def test_send_instructor_email_digests_doesnt_send_empty_digests(
        self, svc, context, mailchimp_service
    ):
        context.instructor_digest.return_value = {"total_annotations": 0}

        svc.send_instructor_email_digests(
            [sentinel.h_userid], sentinel.updated_after, sentinel.updated_before
        )

        mailchimp_service.send_template.assert_not_called()

    def test_send_instructor_email_digests_ignores_instructors_with_no_email_address(
        self, svc, context, mailchimp_service
    ):
        context.unified_users = {sentinel.h_userid: UnifiedUserFactory(email=None)}
        context.instructor_digest.return_value = {"total_annotations": 1}

        svc.send_instructor_email_digests(
            [sentinel.h_userid], sentinel.updated_after, sentinel.updated_before
        )

        mailchimp_service.send_template.assert_not_called()

    def test_send_instructor_email_digests_uses_override_to_email(
        self, svc, context, mailchimp_service
    ):
        context.instructor_digest.return_value = {"total_annotations": 1}

        svc.send_instructor_email_digests(
            [sentinel.h_userid],
            sentinel.updated_after,
            sentinel.updated_before,
            override_to_email=sentinel.override_to_email,
        )

        assert (
            mailchimp_service.send_template.call_args[1]["recipient"].email
            == sentinel.override_to_email
        )

    @pytest.fixture(autouse=True)
    def DigestContext(self, patch):
        return patch("lms.services.digest.service.DigestContext")

    @pytest.fixture
    def context(self, DigestContext):
        return DigestContext.return_value

    @pytest.fixture
    def sender(self):
        return EmailSender(sentinel.subaccount, sentinel.from_email, sentinel.from_name)

    @pytest.fixture
    def svc(self, db_session, h_api, mailchimp_service, sender):
        return DigestService(
            db=db_session,
            h_api=h_api,
            mailchimp_service=mailchimp_service,
            sender=sender,
        )


class UnifiedUserFactory(factory.Factory):
    class Meta:
        model = UnifiedUser

    h_userid = factory.Sequence(lambda n: f"acct:user_{n}@lms.hypothes.is")
    users = factory.LazyAttribute(
        lambda o: factories.User.create_batch(2, h_userid=o.h_userid)
    )
    email = factory.Sequence(lambda n: f"user_{n}@example.com")
    display_name = factory.Sequence(lambda n: f"User {n}")
