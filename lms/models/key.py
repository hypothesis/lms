from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from lms.db import BASE
from lms.models import CreatedUpdatedMixin


class Key(CreatedUpdatedMixin, BASE):
    __tablename__ = "key"

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    kid = sa.Column(
        UUID(as_uuid=True),
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

    def private_key(self, secret):
        from lms.services import aes

        return aes.decrypt(secret, self.aes_cipher_iv, self._private_key)

    @property
    def jwk(self):
        import json

        jwk = json.loads(self.public_key)
        jwk["kid"] = self.kid.hex
        jwk["use"] = "sig"
        return jwk
