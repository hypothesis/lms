from datetime import timedelta
from unittest.mock import sentinel

import pytest

from lms.models import EmailUnsubscribe
from lms.services.email_unsubscribe import EmailUnsubscribeService, factory


class TestEmailUnsubscribeService:
    def test_unsubscribe_url(self, svc, jwt_service):
        jwt_service.encode_with_secret.return_value = "TOKEN"

        url = svc.unsubscribe_url(sentinel.email, sentinel.tag)

        jwt_service.encode_with_secret.assert_called_once_with(
            {"h_userid": sentinel.email, "tag": sentinel.tag},
            "SECRET",
            lifetime=timedelta(days=30),
        )
        assert url == "http://example.com/email/unsubscribe?token=TOKEN"

    def test_unsubscribe(self, svc, bulk_upsert, jwt_service, db_session):
        jwt_service.decode_with_secret.return_value = {
            "h_userid": sentinel.h_userid,
            "tag": sentinel.tag,
        }

        svc.unsubscribe(sentinel.token)

        jwt_service.decode_with_secret.assert_called_once_with(sentinel.token, "SECRET")
        bulk_upsert.assert_called_once_with(
            db_session,
            model_class=EmailUnsubscribe,
            values=[
                {
                    "h_userid": sentinel.h_userid,
                    "tag": sentinel.tag,
                }
            ],
            index_elements=["h_userid", "tag"],
            update_columns=["updated"],
        )

    @pytest.fixture
    def svc(self, db_session, jwt_service, pyramid_request):
        return EmailUnsubscribeService(
            db_session, jwt_service, "SECRET", pyramid_request.route_url
        )

    @pytest.fixture
    def bulk_upsert(self, patch):
        return patch("lms.services.email_unsubscribe.bulk_upsert")


class TestFactory:
    def test_it(
        self, pyramid_request, EmailUnsubscribeService, db_session, jwt_service
    ):
        svc = factory(sentinel.context, pyramid_request)

        EmailUnsubscribeService.assert_called_once_with(
            db_session,
            jwt_service,
            secret="test_secret",
            route_url=pyramid_request.route_url,
        )
        assert svc == EmailUnsubscribeService.return_value

    @pytest.fixture
    def EmailUnsubscribeService(self, patch):
        return patch("lms.services.email_unsubscribe.EmailUnsubscribeService")
