from datetime import datetime
from unittest import mock

import pytest
from h_matchers import Any
from pytest import param

from lms.db import LockType, TryLockError
from lms.models import OAuth2Token
from lms.services import OAuth2TokenError
from lms.services.oauth2_token import (
    OAuth2TokenService,
    Service,
    oauth2_token_service_factory,
)
from tests import factories


@pytest.mark.usefixtures("application_instance")
class TestOAuth2TokenService:
    @pytest.mark.usefixtures("oauth_token_in_db_or_not")
    @pytest.mark.parametrize("service", [Service.LMS, Service.CANVAS_STUDIO])
    def test_save(self, application_instance, lti_user, service, save_token):
        oauth2_token = save_token(service)
        assert oauth2_token == Any.object(OAuth2Token).with_attrs(
            {
                "application_instance_id": application_instance.id,
                "user_id": lti_user.user_id,
                "access_token": "access_token",
                "refresh_token": "refresh_token",
                "expires_in": 1234,
                "received_at": Any.instance_of(datetime),
                "service": service,
            }
        )

    @pytest.mark.parametrize("service", [Service.LMS, Service.CANVAS_STUDIO])
    def test_get_returns_token_when_present(
        self, db_session, lti_user, application_instance, svc, service
    ):
        oauth_token = factories.OAuth2Token.build(
            user_id=lti_user.user_id,
            application_instance=application_instance,
            service=service,
        )
        db_session.add(oauth_token)

        result = svc.get(service)

        assert result == oauth_token

    def test_get_raises_OAuth2TokenError_with_mismatching_application_instance(
        self, db_session, lti_user
    ):
        service = OAuth2TokenService(
            db_session,
            application_instance=factories.ApplicationInstance(),
            user_id=lti_user.user_id,
        )

        with pytest.raises(OAuth2TokenError):
            service.get()

    def test_get_raises_OAuth2TokenError_with_mismatching_user(
        self, db_session, application_instance
    ):
        service = OAuth2TokenService(
            db_session, application_instance=application_instance, user_id="WRONG"
        )

        with pytest.raises(OAuth2TokenError):
            service.get()

    @pytest.fixture(
        params=(param(True, id="token in db"), param(False, id="token not in db"))
    )
    def oauth_token_in_db_or_not(
        self, request, db_session, lti_user, application_instance
    ):
        """Get an OAuthToken or None based on the fixture params."""
        oauth_token = None
        if request.param:
            oauth_token = factories.OAuth2Token.build(
                user_id=lti_user.user_id,
                application_instance=application_instance,
            )

            db_session.add(oauth_token)

        return oauth_token

    def test_try_lock_for_refresh(
        self,
        pyramid_request,
        svc,
        try_advisory_transaction_lock,
        save_token,
    ):
        oauth2_token = save_token()

        # Successful lock
        svc.try_lock_for_refresh(Service.LMS)
        try_advisory_transaction_lock.assert_called_with(
            pyramid_request.db, LockType.OAUTH2_TOKEN_REFRESH, oauth2_token.id
        )

        # If locking fails, the service should propagate the exception
        try_advisory_transaction_lock.side_effect = TryLockError()
        with pytest.raises(TryLockError):
            svc.try_lock_for_refresh(Service.LMS)

    @pytest.fixture
    def svc(self, pyramid_request, application_instance):
        return OAuth2TokenService(
            pyramid_request.db,
            application_instance,
            pyramid_request.lti_user.user_id,
        )

    @pytest.fixture
    def save_token(self, db_session, svc):
        def save_token(service=Service.LMS):
            svc.save(
                access_token="access_token",
                refresh_token="refresh_token",
                expires_in=1234,
                service=service,
            )
            return db_session.query(OAuth2Token).filter_by(service=service).one()

        return save_token

    @pytest.fixture
    def try_advisory_transaction_lock(self, patch):
        return patch("lms.services.oauth2_token.try_advisory_transaction_lock")


class TestOAuth2TokenServiceFactory:
    def test_it(self, pyramid_request):
        svc = oauth2_token_service_factory(mock.sentinel.context, pyramid_request)

        assert isinstance(svc, OAuth2TokenService)
