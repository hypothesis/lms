import copy
import datetime
import json
from unittest.mock import create_autospec, sentinel

import httpretty
import jwt
import pytest
from freezegun import freeze_time
from jwt.exceptions import InvalidTokenError
from pyramid.config import Configurator
from pytest import param

from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.services.jwt import JWTService, _get_lti_jwt, factory, includeme
from tests import factories


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

    def test_decode_lti_token(self, svc, jwt, lti_registration_service):
        registration = factories.LTIRegistration(key_set_url="http://jwk.com")
        lti_registration_service.get.return_value = registration
        jwt.decode.return_value = {"aud": "AUD", "iss": "ISS"}

        payload = svc.decode_lti_token(sentinel.id_token)

        lti_registration_service.get.assert_called_once_with("ISS", "AUD")
        jwt.PyJWKClient.assert_called_once_with(
            lti_registration_service.get.return_value.key_set_url
        )
        jwt.decode.assert_called_with(
            sentinel.id_token,
            key=jwt.PyJWKClient.return_value.get_signing_key_from_jwt.return_value.key,
            audience="AUD",
            algorithms=["RS256"],
        )
        assert payload == {"aud": "AUD", "iss": "ISS"}

    def test_decode_lti_token_with_empty_token(self, svc):
        assert not svc.decode_lti_token("")

    def test_decode_lti_token_with_no_kid(self, svc):
        jwt_str = self.encode_jwt({"key": "value"}, headers={"key": "value"})

        assert not svc.decode_lti_token(jwt_str)

    def test_decode_lti_token_with_no_registration(
        self, svc, jwt, lti_registration_service
    ):
        jwt.decode.return_value = {"aud": "AUD", "iss": "ISS"}
        lti_registration_service.get.return_value = None

        assert not svc.decode_lti_token(sentinel.id_token)

    def test_decode_lti_token_with_invalid_jwt(self, svc, jwt):
        jwt.decode.side_effect = [{"aud": "AUD", "iss": "ISS"}, InvalidTokenError()]

        assert not svc.decode_lti_token(sentinel.id_token)

    @staticmethod
    def encode_jwt(
        payload,
        secret="test_secret",
        algorithm="HS256",
        headers=None,
        lifetime=None,
    ):
        """Return payload encoded to a jwt with secret and algorithm."""
        payload = copy.deepcopy(payload)

        if lifetime:
            payload["exp"] = datetime.datetime.utcnow() + lifetime

        return jwt.encode(payload, secret, algorithm=algorithm, headers=headers)

    @pytest.fixture(autouse=True)
    def jwk_endpoint(self):
        keys = {"keys": [{"kid": "KID", "kty": "RSA", "n": "1000", "e": "500"}]}

        httpretty.register_uri("GET", "http://jwk.com", body=json.dumps(keys))

    @pytest.fixture()
    def jwt(self, patch):
        return patch("lms.services.jwt.jwt")

    @pytest.fixture
    def svc(self, lti_registration_service):
        svc = JWTService(lti_registration_service)
        # Clear the lru_cache to make tests independent
        svc._get_jwk_client.cache_clear()  # pylint: disable=protected-access
        return svc


class TestFactory:
    def test_it(self, pyramid_request, JWTService, lti_registration_service):
        jwt_service = factory(sentinel.context, pyramid_request)

        JWTService.assert_called_once_with(lti_registration_service)
        assert jwt_service == JWTService.return_value

    @pytest.fixture
    def JWTService(self, patch):
        return patch("lms.services.jwt.JWTService")


class TestGetLTIJWT:
    def test_it(self, jwt_service, pyramid_request):
        pyramid_request.params["id_token"] = "JWT"

        jwt_params = _get_lti_jwt(pyramid_request)

        jwt_service.decode_lti_token.assert_called_with(
            pyramid_request.params["id_token"]
        )
        assert jwt_params == jwt_service.decode_lti_token.return_value


class TestIncludeMe:
    def test_it_sets_lti_jwt(self, configurator):
        includeme(configurator)

        configurator.add_request_method.assert_called_once_with(
            _get_lti_jwt, name="lti_jwt", property=True, reify=True
        )

    @pytest.fixture()
    def configurator(self):
        return create_autospec(Configurator, spec_set=True, instance=True)
