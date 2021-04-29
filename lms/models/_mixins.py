import datetime

import sqlalchemy as sa


class TimestampedModelMixin:
    created = sa.Column(
        sa.DateTime(),
        server_default=sa.func.now(),
        default=datetime.datetime.utcnow,
        nullable=False,
    )
    updated = sa.Column(
        sa.DateTime(),
        default=datetime.datetime.utcnow,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )
