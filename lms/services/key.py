import json

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from jose import constants, jwk
from sqlalchemy import func

from lms.models import Key
from lms.services import aes


class KeyService:
    def __init__(self, db):
        self._db = db

    def generate(self, aes_secret) -> Key:
        key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        pem_private_key = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            # We could specify encryption here and avoid having to do the AES ourselves
            encryption_algorithm=serialization.NoEncryption(),
        )

        iv = aes.build_iv()
        aes_pem_private_key = aes.encrypt(aes_secret, iv, pem_private_key)

        pem_public_key = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        jwk_public_key = jwk.RSAKey(
            algorithm=constants.Algorithms.RS256, key=pem_public_key.decode("utf-8")
        ).to_dict()

        key = Key(
            _private_key=aes_pem_private_key,
            public_key=json.dumps(jwk_public_key),
            aes_cipher_iv=iv,
        )
        self._db.add(key)
        return key

    def all(self):
        """all valid in the real version"""
        return self._db.query(Key).all()

    def one(self):
        """Get one at random to spread usage of the valid keys"""
        return self._db.query(Key).order_by(func.random()).first()


def factory(_context, request):
    return KeyService(
        request.db,
    )
