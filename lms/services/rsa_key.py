import json

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import constants, jwk

from lms.models import RSAKey
from lms.services import AESService


class RSAKeyService:
    no_encryption = serialization.NoEncryption()

    def __init__(self, db, aes_service):
        self._db = db
        self._aes_service = aes_service

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
        """Get all non-expired keys."""
        return [
            dict(json.loads(key.public_key), use="sig", kid=key.kid)
            for key in self._db.query(RSAKey).filter_by(expired=False).all()
        ]

    def _as_pem_private_key(self, rsa_key, aes_iv) -> bytes:
        """Encode a `jose.jwt.RSAKey` as an AES encrypted PEM private key."""
        pem_private_key = rsa_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=self.no_encryption,
        )
        return self._aes_service.encrypt(aes_iv, pem_private_key)

    @staticmethod
    def _as_jwk_public_key(rsa_key) -> dict:
        """Encode a `jose.jwt.RSAKey` as a JWK public key."""
        pem_public_key = rsa_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return jwk.RSAKey(
            algorithm=constants.Algorithms.RS256, key=pem_public_key.decode("utf-8")
        ).to_dict()


def factory(_context, request):
    return RSAKeyService(request.db, request.find_service(AESService))
