import sqlalchemy as sa


class CreatedUpdatedMixin:
    created = sa.Column(
        sa.DateTime(),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated = sa.Column(
        sa.DateTime(),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )
