import uuid

import sqlalchemy as sa

from lms.db import BASE
from lms.models import CreatedUpdatedMixin


class RSAKey(CreatedUpdatedMixin, BASE):
    __tablename__ = "rsa_key"

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    kid = sa.Column(sa.Unicode, default=lambda: uuid.uuid4().hex, nullable=False)
    """Unique identifier exposed to third parties"""

    public_key = sa.Column(sa.Unicode)
    """Public key a json JWK string"""

    private_key = sa.Column(sa.LargeBinary)
    """PEM formatted private key. AES encrypted"""

    aes_cipher_iv = sa.Column(sa.LargeBinary)
    """IV for the private key AES encryption"""

    expired = sa.Column(
        sa.Boolean(),
        default=False,
        server_default=sa.sql.expression.false(),
        nullable=False,
    )
    """Marks the key as expired"""
