from unittest.mock import create_autospec, patch, sentinel

import pytest

from lms.services.digest._digest_assistant import DigestAssistant
from lms.services.digest._models import Digest, HCourse, HUser
from lms.services.digest.service import DigestService
from lms.services.mailchimp import EmailSender


class TestDigestService:
    def test_send_emails(self, svc, get_digests, mailchimp_service, digest, sender):
        svc.send_emails(sentinel.audience, sentinel.after, sentinel.before)

        get_digests.assert_called_once_with(
            sentinel.audience, sentinel.after, sentinel.before
        )
        mailchimp_service.send_template.assert_called_once_with(
            template_name="instructor-email-digest",
            sender=sender,
            recipient=digest.audience_user,
            template_vars=digest.serialize(),
        )

    @pytest.mark.usefixtures("get_digests")
    @pytest.mark.parametrize(
        "user_email,override_to_email,send_email",
        (
            ("email@example.com", None, "email@example.com"),
            (None, "OVERRIDE@example.com", "OVERRIDE@example.com"),
            ("email@example.com", "OVERRIDE@example.com", "OVERRIDE@example.com"),
            (None, None, None),
        ),
    )
    def test_send_email_destination(
        self, svc, digest, mailchimp_service, user_email, override_to_email, send_email
    ):
        digest.audience_user.email = user_email

        svc.send_emails(
            sentinel.audience,
            sentinel.after,
            sentinel.before,
            override_to_email=override_to_email,
        )

        if send_email:
            assert digest.audience_user.email == send_email
            mailchimp_service.send_template.assert_called_once()
        else:
            mailchimp_service.send_template.assert_not_called()

    def test_send_email_requires_some_annotations(self, svc, digest, mailchimp_service):
        digest.courses[0].annotations = []

        svc.send_emails(sentinel.audience, sentinel.after, sentinel.before)

        mailchimp_service.send_template.assert_not_called()

    def test_get_digests(self, svc, h_api, digest_assistant):
        # The most minimal happy path
        annotations = [
            {
                "group": {"authority_provided_id": "123"},
                "author": {"userid": "acct:learner"},
            },
            {
                "group": {"authority_provided_id": "456"},
                "author": {"userid": "acct:learner"},
            },
        ]
        audience_user = HUser(h_userid="acct:audience", name="Aud 1", email="email@1")
        course = HCourse(
            title="course",
            authority_provided_id="123",
            aka=["123", "456"],
            instructors=["acct:audience"],
        )
        h_api.get_annotations.return_value = annotations
        digest_assistant.get_h_users.return_value = [audience_user]
        digest_assistant.get_h_courses.return_value = [course]
        audience = [audience_user.h_userid, "acct:red-herring"]

        results = list(svc.get_digests(audience, sentinel.after, sentinel.before))

        h_api.get_annotations.assert_called_once_with(
            audience, sentinel.after, sentinel.before
        )
        digest_assistant.get_h_courses.assert_called_once_with(
            authority_provided_ids={"123", "456"}
        )
        assert course.annotations == annotations
        digest_assistant.get_h_users.assert_called_once_with(h_userids=audience)

        assert results == [Digest(audience_user=audience_user, courses=[course])]

    def test_get_digests_requires_some_annotations(self, svc, h_api, digest_assistant):
        h_api.get_annotations.return_value = []

        result = list(
            svc.get_digests(sentinel.audience, sentinel.after, sentinel.before)
        )

        digest_assistant.get_h_courses.assert_not_called()
        assert not result

    @pytest.fixture
    def digest(self):
        return Digest(
            audience_user=HUser(h_userid="acct:name", name="Name", email="email@1"),
            courses=[
                HCourse(
                    title="name",
                    authority_provided_id="aid",
                    aka=["aid"],
                    instructors=["acct:instructor"],
                    annotations=[{"author": {"userid": "acct:student"}}],
                )
            ],
        )

    @pytest.fixture
    def get_digests(self, svc, digest):
        with patch.object(svc, "get_digests") as get_digests:
            get_digests.return_value = [digest]
            yield get_digests

    @pytest.fixture
    def sender(self):
        return EmailSender(sentinel.subaccount, sentinel.from_email, sentinel.from_name)

    @pytest.fixture
    def digest_assistant(self):
        return create_autospec(DigestAssistant, spec_set=True, instance=True)

    @pytest.fixture
    def svc(self, digest_assistant, h_api, mailchimp_service, sender):
        return DigestService(
            digest_assistant=digest_assistant,
            h_api=h_api,
            mailchimp_service=mailchimp_service,
            sender=sender,
        )
