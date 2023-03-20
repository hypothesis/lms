from unittest.mock import sentinel

import pytest

from lms.services.digest import service_factory
from lms.services.mailchimp import EmailSender


class TestServiceFactory:
    def test_it(self, pyramid_request, h_api, mailchimp_service, DigestService):
        settings = pyramid_request.registry.settings
        settings["mailchimp_digests_subaccount"] = sentinel.digests_subaccount
        settings["mailchimp_digests_email"] = sentinel.digests_from_email
        settings["mailchimp_digests_name"] = sentinel.digests_from_name

        service = service_factory(sentinel.context, pyramid_request)

        DigestService.assert_called_once_with(
            db=pyramid_request.db,
            h_api=h_api,
            mailchimp_service=mailchimp_service,
            sender=EmailSender(
                sentinel.digests_subaccount,
                sentinel.digests_from_email,
                sentinel.digests_from_name,
            ),
        )
        assert service == DigestService.return_value

    @pytest.fixture
    def DigestService(self, patch):
        return patch("lms.services.digest.factory.DigestService")
