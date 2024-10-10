from unittest.mock import sentinel

import pytest

from lms.models import LTIRegistration
from lms.services.lti_registration import LTIRegistrationService, factory
from tests import factories


class TestLTIRegistrationService:
    def test_get(self, svc, registration):
        assert svc.get(registration.issuer, registration.client_id) == registration

    @pytest.mark.usefixtures("registration")
    def test_get_none_issuer(self, svc):
        assert not svc.get(None)

    def test_get_without_client_id(self, svc, registration):
        assert svc.get(registration.issuer) == registration

    def test_create(self, svc, db_session):
        registration = svc.create_registration(
            "ISSUER", "CLIENT_ID", "AUTH_LOGIN_URL", "KEY_SET_URL", "TOKEN_URL"
        )

        assert (
            db_session.query(LTIRegistration)
            .filter_by(issuer="ISSUER", client_id="CLIENT_ID")
            .one()
            == registration
        )

    def test_get_by_id(self, svc, registration, db_session):
        # Force the registration to have an ID
        db_session.flush()

        assert svc.get_by_id(registration.id) == registration

    def test_search_registrations(self, svc):
        # With a known issuer
        factories.LTIRegistration.create_batch(size=5, issuer="issuer")
        # With a known client_id
        factories.LTIRegistration.create_batch(size=5, client_id="client_id")
        # With both a known issuer and client_id (only one as that's the unique key)
        factories.LTIRegistration.create(client_id="client_id", issuer="issuer")

        by_issuer = svc.search_registrations(issuer="issuer")
        assert len(by_issuer) == 6
        assert all(registration.issuer == "issuer" for registration in by_issuer)

        by_client_id = svc.search_registrations(client_id="client_id")
        assert len(by_client_id) == 6
        assert all(
            registration.client_id == "client_id" for registration in by_client_id
        )

        by_both = svc.search_registrations(issuer="issuer", client_id="client_id")
        assert len(by_both) == 1
        assert by_both[0].issuer == "issuer"
        assert by_both[0].client_id == "client_id"

    @pytest.fixture
    def registration(self):
        factories.LTIRegistration.create_batch(4)
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
