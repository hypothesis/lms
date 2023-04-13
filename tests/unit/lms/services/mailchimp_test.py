import logging
from unittest.mock import Mock, sentinel

import pytest
from h_matchers import Any

from lms.services.mailchimp import (
    EmailRecipient,
    EmailSender,
    MailchimpError,
    MailchimpService,
    factory,
)


class TestSendTemplate:
    def test_it(self, mailchimp_transactional, caplog):
        caplog.set_level(logging.INFO)
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

        assert caplog.record_tuples == [
            (
                "lms.services.mailchimp",
                logging.INFO,
                Any.string.matching(
                    r"^mailchimp_client\.send_template\({'template_name': sentinel.template_name,"
                ),
            )
        ]
        mailchimp_transactional.Client.assert_called_once_with(sentinel.api_key)
        mailchimp_transactional.Client.return_value.messages.send_template.assert_called_once_with(
            {
                "template_name": sentinel.template_name,
                "template_content": [{}],
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
                    "headers": {},
                },
                "async": True,
            }
        )

    def test_with_unsubscribe_url(self, mailchimp_transactional):
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
            {},
            sentinel.unsubscribe_url,
        )

        mailchimp_transactional.Client.return_value.messages.send_template.assert_called_once_with(
            Any.dict.containing(
                {
                    "message": Any.dict.containing(
                        {
                            "headers": {
                                "List-Unsubscribe": sentinel.unsubscribe_url,
                            },
                            "global_merge_vars": [
                                {
                                    "name": "unsubscribe_url",
                                    "content": sentinel.unsubscribe_url,
                                }
                            ],
                        }
                    )
                }
            )
        )

    def test_if_mailchimp_client_raises(self, mailchimp_client):
        original_exception = RuntimeError("Mailchimp crashed!")
        mailchimp_client.messages.send_template.side_effect = original_exception

        svc = MailchimpService(sentinel.api_key)

        with pytest.raises(MailchimpError) as exc_info:
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
        assert exc_info.value.__cause__ == original_exception

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
