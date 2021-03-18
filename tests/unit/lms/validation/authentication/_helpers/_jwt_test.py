import copy
import datetime

import jwt
import pytest

from lms.validation.authentication._helpers import _jwt


class TestDecodeJWT:
    def test_it_returns_the_decoded_payload(self):
        original_payload = {"TEST_KEY": "TEST_VALUE"}
        jwt_str = self.encode_jwt(original_payload)

        decoded_payload = _jwt.decode_jwt(jwt_str, "test_secret")

        assert decoded_payload == original_payload

    def test_it_raises_if_the_jwt_is_encoded_with_the_wrong_secret(self):
        jwt_str = self.encode_jwt({"TEST_KEY": "TEST_VALUE"}, secret="wrong_secret")

        with pytest.raises(_jwt.InvalidJWTError):
            _jwt.decode_jwt(jwt_str, "test_secret")

    def test_it_raises_if_the_jwt_is_encoded_with_the_wrong_algorithm(self):
        jwt_str = self.encode_jwt({"TEST_KEY": "TEST_VALUE"}, algorithm="HS384")

        with pytest.raises(_jwt.InvalidJWTError):
            _jwt.decode_jwt(jwt_str, "test_secret")

    def test_it_raises_if_the_jwt_has_expired(self):
        jwt_str = self.encode_jwt(
            {
                "TEST_KEY": "TEST_VALUE",
                "exp": datetime.datetime.utcnow() - datetime.timedelta(hours=1),
            }
        )

        with pytest.raises(_jwt.ExpiredJWTError):
            _jwt.decode_jwt(jwt_str, "test_secret")

    def test_it_raises_if_the_jwt_has_no_expiry_time(self):
        jwt_str = self.encode_jwt({"TEST_KEY": "TEST_VALUE"}, omit_exp=True)

        with pytest.raises(_jwt.InvalidJWTError):
            _jwt.decode_jwt(jwt_str, "test_secret")

    def test_it_can_decode_a_jwt_from_encode_jwt(self):
        original_payload = {"TEST_KEY": "TEST_VALUE"}
        jwt_str = _jwt.encode_jwt(original_payload, "test_secret")

        decoded_payload = _jwt.decode_jwt(jwt_str, "test_secret")

        assert decoded_payload == original_payload

    def encode_jwt(self, payload, omit_exp=False, secret=None, algorithm=None):
        """Return payload encoded to a jwt with secret and algorithm."""
        payload = copy.deepcopy(payload)

        if not omit_exp:
            # Insert an unexpired expiry time into the given payload dict, if
            # it doesn't already contain an expiry time.
            payload.setdefault(
                "exp", datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            )

        jwt_str = jwt.encode(
            payload, secret or "test_secret", algorithm=algorithm or "HS256"
        )

        return jwt_str


class TestEncodeJWT:
    def test_it_returns_the_encoded_jwt(self):
        original_payload = {"TEST_KEY": "TEST_VALUE"}

        jwt_str = _jwt.encode_jwt(original_payload, "test_secret")

        decoded_payload = jwt.decode(jwt_str, "test_secret", algorithms=["HS256"])

        del decoded_payload["exp"]
        assert decoded_payload == original_payload

    def test_it_returns_a_string_not_bytes(self):
        jwt_str = _jwt.encode_jwt({"TEST_KEY": "TEST_VALUE"}, "test_secret")

        assert isinstance(jwt_str, str)

    def test_it_uses_one_hour_lifetime_by_default(self):
        jwt_str = _jwt.encode_jwt({}, "test_secret")
        decoded_payload = jwt.decode(jwt_str, "test_secret", algorithms=["HS256"])
        lifetime_minutes = self._jwt_lifetime(decoded_payload) / 60

        assert round(lifetime_minutes) == 60

    def test_it_uses_custom_lifetime(self):
        jwt_str = _jwt.encode_jwt(
            {}, "test_secret", lifetime=datetime.timedelta(hours=24)
        )
        decoded_payload = jwt.decode(jwt_str, "test_secret", algorithms=["HS256"])
        lifetime_hours = self._jwt_lifetime(decoded_payload) / (60 * 60)

        assert round(lifetime_hours) == 24

    @staticmethod
    def _jwt_lifetime(payload):
        now = datetime.datetime.utcnow().timestamp()
        return payload["exp"] - now
