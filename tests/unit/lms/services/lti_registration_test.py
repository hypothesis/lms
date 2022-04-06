from unittest.mock import sentinel

import pytest

from lms.services.lti_registration import LTIRegistrationService, factory
from tests import factories


class TestLTIRegistrationService:
    def test_get(self, svc, registration):
        assert svc.get(registration.issuer, registration.client_id) == registration

    def test_without_client_id(self, svc, registration):
        assert svc.get(registration.issuer) == registration

    @pytest.fixture
    def registration(self):
        return factories.LTIRegistration()

    @pytest.fixture
    def svc(self, db_session):
        return LTIRegistrationService(db_session)


class TestFactory:
    def test_it(self, pyramid_request, LTIRegistrationService):
        service = factory(sentinel.context, pyramid_request)

        LTIRegistrationService.assert_called_once_with(pyramid_request.db)

        assert service == LTIRegistrationService.return_value

    @pytest.fixture
    def LTIRegistrationService(self, patch):
        return patch("lms.services.lti_registration.LTIRegistrationService")
