import logging
from unittest.mock import Mock, call, sentinel

import pytest
from h_matchers import Any

from lms.services.digest import (
    CourseDigest,
    CourseGroupings,
    InstructorDigest,
    UserRecords,
)
from lms.services.h_api import Annotation, Group, User
from lms.services.mailchimp import (
    EmailRecipient,
    EmailSender,
    MailchimpService,
    factory,
)
from tests import factories


class TestSendTemplate:
    def test_it(self, svc, mailchimp_transactional):
        svc.send_template(
            sentinel.template_name,
            EmailSender(
                sentinel.subaccount_id,
                sentinel.from_email,
                sentinel.from_name,
            ),
            EmailRecipient(
                sentinel.to_email,
                sentinel.to_name,
            ),
            sentinel.merge_vars,
        )

        mailchimp_transactional.Client.assert_called_once_with(sentinel.api_key)
        mailchimp_transactional.Client.return_value.messages.send_template.assert_called_once_with(
            {
                "template_name": sentinel.template_name,
                "message": {
                    "subaccount": sentinel.subaccount_id,
                    "from_email": sentinel.from_email,
                    "from_name": sentinel.from_name,
                    "to": [{"email": sentinel.to_email, "name": sentinel.to_name}],
                    "track_opens": True,
                    "track_clicks": True,
                    "global_merge_vars": sentinel.merge_vars,
                },
                "async": True,
            }
        )

    def test_if_theres_no_api_key_it_prints_the_email(
        self, svc, mailchimp_transactional, caplog
    ):
        svc.api_key = None
        caplog.set_level(logging.INFO)

        svc.send_template(
            sentinel.template_name,
            EmailSender(
                sentinel.subaccount_id,
                sentinel.from_email,
                sentinel.from_name,
            ),
            EmailRecipient(
                sentinel.to_email,
                sentinel.to_name,
            ),
            sentinel.merge_vars,
        )

        mailchimp_transactional.Client.assert_not_called()
        assert caplog.record_tuples == [
            (
                "lms.services.mailchimp",
                logging.INFO,
                Any.string.matching("^{'template_name': sentinel.template_name,"),
            )
        ]


class TestSendInstructorDigests:
    def test_it(self, svc, mailchimp_transactional):
        annotator = UserRecords(
            h_userid=sentinel.annotator,
            user_records=[factories.User.build(h_userid=sentinel.annotator)],
        )
        course = factories.Course()
        annotations = [
            Annotation(
                user=annotator,
                group=Group(authority_provided_id=course.authority_provided_id),
            )
            for _ in range(2)
        ]
        instructors = [
            UserRecords(
                h_userid=sentinel.instructor_1,
                user_records=[
                    factories.User.build(
                        h_userid=sentinel.instructor_1,
                        email=sentinel.email_1,
                        display_name=sentinel.display_name_1,
                    )
                ],
            ),
            UserRecords(
                h_userid=sentinel.instructor_2,
                user_records=[
                    factories.User.build(
                        h_userid=sentinel.instructor_2,
                        email=sentinel.email_2,
                        display_name=sentinel.display_name_2,
                    )
                ],
            ),
        ]
        digests = {
            instructor.h_userid: InstructorDigest(
                instructor,
                courses={
                    course.authority_provided_id: CourseDigest(
                        course=CourseGroupings([course]),
                        users={User(username=annotator.h_userid): annotations},
                    )
                },
            )
            for instructor in instructors
        }

        svc.send_instructor_digests(digests)

        assert (
            mailchimp_transactional.Client.return_value.messages.send_template.call_args_list
            == Any.list.containing(
                [
                    call(
                        {
                            "template_name": "instructor_digest",
                            "message": {
                                "subaccount": sentinel.digests_subaccount,
                                "from_email": sentinel.digests_from_email,
                                "from_name": sentinel.digests_from_name,
                                "to": [
                                    {
                                        "email": sentinel.email_1,
                                        "name": sentinel.display_name_1,
                                    }
                                ],
                                "track_opens": True,
                                "track_clicks": True,
                                "global_merge_vars": [
                                    {"name": "num_annotations", "content": 2},
                                    {
                                        "name": "courses",
                                        "content": [
                                            {
                                                "title": course.lms_name,
                                                "num_annotations": 2,
                                            }
                                        ],
                                    },
                                ],
                            },
                            "async": True,
                        }
                    ),
                    call(
                        {
                            "template_name": "instructor_digest",
                            "message": {
                                "subaccount": sentinel.digests_subaccount,
                                "from_email": sentinel.digests_from_email,
                                "from_name": sentinel.digests_from_name,
                                "to": [
                                    {
                                        "email": sentinel.email_2,
                                        "name": sentinel.display_name_2,
                                    }
                                ],
                                "track_opens": True,
                                "track_clicks": True,
                                "global_merge_vars": [
                                    {"name": "num_annotations", "content": 2},
                                    {
                                        "name": "courses",
                                        "content": [
                                            {
                                                "title": course.lms_name,
                                                "num_annotations": 2,
                                            }
                                        ],
                                    },
                                ],
                            },
                            "async": True,
                        }
                    ),
                ]
            ).only()
        )


@pytest.fixture
def svc():
    return MailchimpService(
        sentinel.api_key,
        digests_sender=EmailSender(
            sentinel.digests_subaccount,
            sentinel.digests_from_email,
            sentinel.digests_from_name,
        ),
    )


class TestFactory:
    def test_it(self, pyramid_request, MailchimpService):
        pyramid_request.registry.settings["mailchimp_api_key"] = sentinel.api_key
        pyramid_request.registry.settings[
            "mailchimp_digests_subaccount"
        ] = sentinel.digests_subaccount
        pyramid_request.registry.settings[
            "mailchimp_digests_email"
        ] = sentinel.digests_from_email
        pyramid_request.registry.settings[
            "mailchimp_digests_name"
        ] = sentinel.digests_from_name

        svc = factory(sentinel.context, pyramid_request)

        MailchimpService.assert_called_once_with(
            sentinel.api_key,
            EmailSender(
                sentinel.digests_subaccount,
                sentinel.digests_from_email,
                sentinel.digests_from_name,
            ),
        )
        assert svc == MailchimpService.return_value

    @pytest.fixture
    def MailchimpService(self, patch):
        return patch("lms.services.mailchimp.MailchimpService")


@pytest.fixture(autouse=True)
def mailchimp_transactional(patch):
    mailchimp_transactional = patch("lms.services.mailchimp.mailchimp_transactional")
    mailchimp_transactional.Client.return_value = Mock(spec_set=["messages"])
    return mailchimp_transactional
