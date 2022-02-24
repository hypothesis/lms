from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from lms.db import BASE
from lms.models import CreatedUpdatedMixin


class Key(CreatedUpdatedMixin, BASE):
    __tablename__ = "key"

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    kid = sa.Column(
        UUID(),
        default=uuid4,
        nullable=False,
    )

    aes_cipher_iv = sa.Column(sa.LargeBinary)

    public_key = sa.Column(sa.Unicode)
    _private_key = sa.Column(sa.LargeBinary)

    expired = sa.Column(
        sa.Boolean(),
        default=False,
        server_default=sa.sql.expression.false(),
        nullable=False,
    )

    @classmethod
    def new(cls):
        import os

        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from jose import constants, jwk

        key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        pem_private_key = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        iv = os.urandom(16)

        # The AES part is duplicated on application_instance. This could be an AES service
        # key = 'request.registry.settings["aes_secret"]'
        key = ""
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        aes_pem_private_key = encryptor.update(pem_private_key) + encryptor.finalize()

        pem_public_key = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        jwk_public_key = jwk.RSAKey(
            algorithm=constants.Algorithms.RS256, key=pem_public_key.decode("utf-8")
        ).to_dict()

        return cls(
            _private_key=aes_pem_private_key, public_key=jwk_public_key, aes_iv=iv
        )
