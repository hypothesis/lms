import copy
import datetime

import jwt
import pytest
from freezegun import freeze_time
from pytest import param

from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.services.jwt import JWTService


class TestJWTService:
    def test_it_can_decode_a_jwt_from_encoded_jwt(self, svc):
        original_payload = {"key": "value"}
        jwt_str = svc.encode_with_secret(
            original_payload, "test_secret", datetime.timedelta(hours=1)
        )

        decoded_payload = svc.decode_with_secret(jwt_str, "test_secret")

        assert decoded_payload == original_payload

    @pytest.mark.parametrize(
        "error,kwargs",
        (
            param(InvalidJWTError, {"secret": "WRONG"}, id="wrong_secret"),
            param(InvalidJWTError, {"algorithm": "HS384"}, id="wrong_algorithm"),
            param(
                ExpiredJWTError,
                {"lifetime": datetime.timedelta(hours=-1)},
                id="already_expired",
            ),
        ),
    )
    def test_decode_raises_for_bad_jwts(self, svc, error, kwargs):
        jwt_params = {"lifetime": datetime.timedelta(hours=24)}
        jwt_params.update(**kwargs)

        jwt_str = self.encode_jwt({"key": "value"}, **jwt_params)

        with pytest.raises(error):
            svc.decode_with_secret(jwt_str, "test_secret")

    @freeze_time("2022-04-04")
    def test_encode_with_secret(self, svc, jwt):
        payload = {"key": "value"}

        encoded_jwt = svc.encode_with_secret(
            payload, "secret", lifetime=datetime.timedelta(hours=1)
        )

        jwt.encode.assert_called_once_with(
            dict(payload, exp=datetime.datetime.utcnow() + datetime.timedelta(hours=1)),
            "secret",
            algorithm="HS256",
        )
        assert encoded_jwt == jwt.encode.return_value

    def encode_jwt(
        self,
        payload,
        lifetime,
        secret="test_secret",
        algorithm="HS256",
    ):
        """Return payload encoded to a jwt with secret and algorithm."""
        payload = copy.deepcopy(payload)

        payload["exp"] = datetime.datetime.utcnow() + lifetime

        return jwt.encode(payload, secret, algorithm=algorithm)

    @pytest.fixture()
    def jwt(self, patch):
        return patch("lms.services.jwt.jwt")

    @pytest.fixture
    def svc(self):
        return JWTService()
