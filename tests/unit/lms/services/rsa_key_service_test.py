from unittest.mock import sentinel

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from h_matchers import Any
from jose import constants

from lms.models import RSAKey
from lms.services.rsa_key import RSAKeyService, factory
from tests import factories


class TestAESService:
    def test_generate(self, svc, aes_service, rsa, jwk):
        jwk.RSAKey.return_value.to_dict.return_value = {}

        key = svc.generate()

        rsa.generate_private_key.assert_called_once_with(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        # Private key
        aes_service.build_iv.assert_called_once_with()
        rsa.generate_private_key.return_value.private_bytes.assert_called_once_with(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=svc.no_encryption,
        )
        aes_service.encrypt.assert_called_once_with(
            aes_service.build_iv.return_value,
            rsa.generate_private_key.return_value.private_bytes.return_value,
        )

        # Public key
        public_bytes = (
            rsa.generate_private_key.return_value.public_key.return_value.public_bytes
        )
        public_bytes.assert_called_once_with(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        jwk.RSAKey.assert_called_once_with(
            algorithm=constants.Algorithms.RS256,
            key=public_bytes.return_value.decode("utf-8"),
        )

        assert key.private_key == aes_service.encrypt.return_value
        assert key.aes_cipher_iv == aes_service.build_iv.return_value

    def test_private_key(self, aes_service, svc):
        key = RSAKey(aes_cipher_iv=sentinel.iv, private_key=sentinel.private_key)

        private_key = svc.private_key(key)

        aes_service.decrypt.assert_called_once_with(sentinel.iv, sentinel.private_key)
        assert private_key == aes_service.decrypt.return_value

    def test_get_all_public_jwks(self, svc, valid_keys):
        keys = svc.get_all_public_jwks()

        expected_keys = [
            {"use": "sig", "kid": key.kid, "key": "value"} for key in valid_keys
        ]
        assert keys == Any.list.containing(expected_keys).only()

    def test_get_random_key(self, svc, valid_keys):
        key = svc.get_random_key()

        assert key in valid_keys

    @pytest.fixture
    def valid_keys(self):
        # Create some noise with some expired keys.
        factories.RSAKey.create_batch(size=3, expired=True)
        return factories.RSAKey.create_batch(
            size=3, expired=False, public_key='{"key": "value"}'
        )

    @pytest.fixture
    def svc(self, db_session, aes_service):
        return RSAKeyService(db_session, aes_service)

    @pytest.fixture
    def jwk(self, patch):
        return patch("lms.services.rsa_key.jwk")

    @pytest.fixture
    def rsa(self, patch):
        return patch("lms.services.rsa_key.rsa")


class TestFactory:
    def test_it(self, pyramid_request, RSAKeyService, aes_service, db_session):
        rsa_key_service = factory(sentinel.context, pyramid_request)

        RSAKeyService.assert_called_once_with(db_session, aes_service)
        assert rsa_key_service == RSAKeyService.return_value

    @pytest.fixture
    def RSAKeyService(self, patch):
        return patch("lms.services.rsa_key.RSAKeyService")
