from unittest.mock import sentinel

import pytest

from lms.services.digest.factory import service_factory
from lms.services.mailchimp import EmailSender


class TestServiceFactory:
    def test_it(
        self, pyramid_request, h_api, mailchimp_service, DigestService, DigestAssistant
    ):
        settings = pyramid_request.registry.settings
        settings["mailchimp_digests_subaccount"] = sentinel.subaccount
        settings["mailchimp_digests_email"] = sentinel.email
        settings["mailchimp_digests_name"] = sentinel.name

        service = service_factory(sentinel.context, pyramid_request)

        DigestAssistant.assert_called_once_with(pyramid_request.db)
        DigestService.assert_called_once_with(
            digest_assistant=DigestAssistant.return_value,
            h_api=h_api,
            mailchimp_service=mailchimp_service,
            sender=EmailSender(
                subaccount=sentinel.subaccount, email=sentinel.email, name=sentinel.name
            ),
        )
        assert service == DigestService.return_value

    @pytest.fixture
    def DigestAssistant(self, patch):
        return patch("lms.services.digest.factory.DigestAssistant")

    @pytest.fixture
    def DigestService(self, patch):
        return patch("lms.services.digest.factory.DigestService")
