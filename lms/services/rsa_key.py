import base64
import json
from datetime import datetime, timedelta

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.utils import int_to_bytes
from sqlalchemy import func

from lms.models import RSAKey
from lms.services.aes import AESService


class RSAKeyService:
    no_encryption = serialization.NoEncryption()

    def __init__(self, db, aes_service):
        self._db = db
        self._aes_service = aes_service

    def rotate(
        self,
        target_keys: int,
        max_age=timedelta(days=7),
        max_expired_age=timedelta(days=14),
    ):
        """
        Rotate RSA Keys keeping `target_keys` active keys at all times.

        Expires active keys older than `max_age`
        and deletes expired ones older than `max_expired_age`.

        Keys have a live-cycle of:
            active -> expired -> deleted

        In flight request we signed with an active key will still be
        verifiable as the public key endpoint query (get_all_public_jwks)
        includes expired keys.

        This method is meant to be called periodically by a celery task.
        """
        now = datetime.now()
        new_keys = target_keys

        for key in self._db.query(RSAKey).all():
            key_age = now - key.created
            # Delete expired keys that have been around for `max_expired_age`
            if key.expired and key_age >= max_expired_age:
                self._db.delete(key)
            # Expire valid keys after max_age
            elif not key.expired and key_age >= max_age:
                key.expired = True
            # Every valid key we see means we need to create one less
            else:
                new_keys -= 1

        for _ in range(new_keys):
            self.generate()

        # Assert the expected result, if we find something different the transition will be aborted
        # and we'd be back at the initial state
        assert (
            self._db.query(RSAKey).filter_by(expired=False).count() == target_keys
        ), "The number of active RSAKey doesn't match the target"

    def generate(self) -> RSAKey:
        """Generate a new random RSA key pair."""
        rsa_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        # Generate an IV for the private key AES encryption
        aes_iv = self._aes_service.build_iv()

        key = RSAKey(
            private_key=self._as_pem_private_key(rsa_key, aes_iv),
            public_key=json.dumps(self._as_jwk_public_key(rsa_key)),
            aes_cipher_iv=aes_iv,
        )
        self._db.add(key)
        return key

    def private_key(self, key: RSAKey):
        """Decrypt the AES encrypted private key of `key`."""
        return self._aes_service.decrypt(key.aes_cipher_iv, key.private_key)

    def get_all_public_jwks(self):
        """
        Get all keys.

        We don't filter out expired ones here to allow in-flight request to
        continue while keys are rotating.
        """
        return [
            dict(json.loads(key.public_key), use="sig", kid=key.kid)
            for key in self._db.query(RSAKey).filter_by().all()
        ]

    def get_random_key(self) -> RSAKey:
        """Get one random key from the valid ones to spread usage between them."""
        return (
            self._db.query(RSAKey)
            .filter_by(expired=False)
            .order_by(func.random())
            .first()
        )

    def _as_pem_private_key(self, rsa_key: rsa.RSAPrivateKey, aes_iv) -> bytes:
        """Encode a rsa key as an AES encrypted PEM private key."""
        pem_private_key = rsa_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=self.no_encryption,
        )
        return self._aes_service.encrypt(aes_iv, pem_private_key)

    @staticmethod
    def _as_jwk_public_key(rsa_key: rsa.RSAPrivateKey) -> dict:
        """Encode a rsa key as a JWK public key."""
        public_key_numbers = rsa_key.public_key().public_numbers()
        return {
            "alg": "RS256",
            "kty": "RSA",
            "n": RSAKeyService._number_to_base_64(public_key_numbers.n),
            "e": RSAKeyService._number_to_base_64(public_key_numbers.e),
        }

    @staticmethod
    def _number_to_base_64(n: int):
        return base64.urlsafe_b64encode(int_to_bytes(n)).strip(b"=").decode("utf-8")


def factory(_context, request):
    return RSAKeyService(request.db, request.find_service(AESService))
