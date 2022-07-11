import datetime
from unittest.mock import sentinel

import pytest
from freezegun import freeze_time

from lms.models import HUser
from lms.services.grant_token import factory
from tests.conftest import TEST_SETTINGS


class TestGrantTokenService:
    @freeze_time("2022-07-11")
    def test_it_generates_valid_jwt_token(self, svc, jwt_service):
        user = HUser(username="abcdef123")
        now = datetime.datetime.now()

        grant_token = svc.generate_token(user)

        jwt_service.encode_with_secret.assert_called_once_with(
            {
                "aud": "example.com",
                "iat": now,
                "iss": TEST_SETTINGS["h_jwt_client_id"],
                "sub": user.userid(TEST_SETTINGS["h_authority"]),
                "nbf": now,
            },
            TEST_SETTINGS["h_jwt_client_secret"],
            lifetime=datetime.timedelta(minutes=5),
        )
        assert grant_token == jwt_service.encode_with_secret.return_value

    @pytest.fixture
    def svc(self, pyramid_request, jwt_service):  # pylint: disable=unused-argument
        return factory(sentinel.context, pyramid_request)
