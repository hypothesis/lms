from datetime import timedelta
from unittest.mock import sentinel

import pytest

from lms.models import EmailUnsubscribe
from lms.services.email_unsubscribe import EmailUnsubscribeService, factory
from tests import factories


class TestEmailUnsubscribeService:
    def test_unsubscribe_url(self, svc, jwt_service):
        jwt_service.encode_with_secret.return_value = "TOKEN"

        url = svc.unsubscribe_url(sentinel.email, sentinel.tag)

        jwt_service.encode_with_secret.assert_called_once_with(
            {"email": sentinel.email, "tag": sentinel.tag},
            "SECRET",
            lifetime=timedelta(days=7),
        )
        assert url == "http://example.com/email/unsubscribe/TOKEN"

    def test_unsubscribe(self, svc, bulk_upsert, jwt_service, db_session):
        jwt_service.decode_with_secret.return_value = {
            "email": sentinel.email,
            "tag": sentinel.tag,
        }

        svc.unsubscribe(sentinel.token)

        jwt_service.decode_with_secret.assert_called_once_with(sentinel.token, "SECRET")
        bulk_upsert.assert_called_once_with(
            db_session,
            model_class=EmailUnsubscribe,
            values=[
                {
                    "email": sentinel.email,
                    "tag": sentinel.tag,
                }
            ],
            index_elements=["email", "tag"],
            update_columns=["updated"],
        )

    @pytest.mark.parametrize(
        "tag,email,expected",
        [
            ("digest", "other@example.com", False),
            ("othertag", "other@example.com", False),
            ("othertag", "example@example.com", False),
            ("digest", "example@example.com", True),
        ],
    )
    def test_is_unsubscribed(self, db_session, svc, email, tag, expected):
        factories.email_unsubscribe.EmailUnsubscribe(
            tag="digest", email="example@example.com"
        )
        db_session.flush()

        assert svc.is_unsubscribed(email, tag) == expected

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
        self,
        pyramid_request,
        EmailUnsubscribeService,
        db_session,
        jwt_service,
        partial,
    ):
        svc = factory(sentinel.context, pyramid_request)

        partial.assert_called_once_with(
            pyramid_request.route_url, _app_url="http://localhost:8001/"
        )
        EmailUnsubscribeService.assert_called_once_with(
            db_session,
            jwt_service,
            secret="test_secret",
            route_url=partial.return_value,
        )
        assert svc == EmailUnsubscribeService.return_value

    @pytest.fixture
    def EmailUnsubscribeService(self, patch):
        return patch("lms.services.email_unsubscribe.EmailUnsubscribeService")

    @pytest.fixture
    def partial(self, patch):
        return patch("lms.services.email_unsubscribe.partial")
