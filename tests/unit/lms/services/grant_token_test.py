import datetime
from unittest.mock import sentinel

import jwt
import pytest

from lms.models import HUser
from lms.services.grant_token import factory
from tests.conftest import TEST_SETTINGS


class TestGrantTokenService:
    def test_it_generates_valid_jwt_token(self, svc):
        before = int(datetime.datetime.now().timestamp())
        user = HUser(username="abcdef123")

        grant_token = svc.generate_token(user)
        secret = TEST_SETTINGS["h_jwt_client_secret"]
        claims = jwt.decode(
            grant_token, secret, audience="example.com", algorithms=["HS256"]
        )

        assert claims["iss"] == TEST_SETTINGS["h_jwt_client_id"]
        assert claims["sub"] == user.userid(TEST_SETTINGS["h_authority"])
        assert claims["nbf"] >= before
        assert claims["exp"] >= before + datetime.timedelta(minutes=5).seconds

    @pytest.fixture
    def svc(self, pyramid_request):
        return factory(sentinel.context, pyramid_request)
