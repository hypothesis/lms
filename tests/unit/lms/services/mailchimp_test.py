import logging
from unittest.mock import Mock, sentinel

import pytest
from h_matchers import Any

from lms.services.mailchimp import (
    EmailRecipient,
    EmailSender,
    MailchimpService,
    factory,
)


class TestSendTemplate:
    def test_it(self, mailchimp_transactional):
        svc = MailchimpService(sentinel.api_key)

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
            template_vars={"foo": "FOO", "bar": "BAR"},
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
                    "global_merge_vars": [
                        {"name": "foo", "content": "FOO"},
                        {"name": "bar", "content": "BAR"},
                    ],
                },
                "async": True,
            }
        )

    def test_if_theres_no_api_key_it_prints_the_email(self, mailchimp_client, caplog):
        svc = MailchimpService(None)
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
            {},
        )

        mailchimp_client.messages.send_template.assert_not_called()
        assert caplog.record_tuples == [
            (
                "lms.services.mailchimp",
                logging.INFO,
                Any.string.matching("^{'template_name': sentinel.template_name,"),
            )
        ]

    @pytest.fixture
    def mailchimp_client(self, mailchimp_transactional):
        return mailchimp_transactional.Client.return_value


class TestFactory:
    def test_it(self, pyramid_request, MailchimpService):
        pyramid_request.registry.settings["mailchimp_api_key"] = sentinel.api_key

        svc = factory(sentinel.context, pyramid_request)

        MailchimpService.assert_called_once_with(sentinel.api_key)
        assert svc == MailchimpService.return_value

    @pytest.fixture
    def MailchimpService(self, patch):
        return patch("lms.services.mailchimp.MailchimpService")


@pytest.fixture(autouse=True)
def mailchimp_transactional(patch):
    mailchimp_transactional = patch("lms.services.mailchimp.mailchimp_transactional")
    mailchimp_transactional.Client.return_value = Mock(spec_set=["messages"])
    return mailchimp_transactional
