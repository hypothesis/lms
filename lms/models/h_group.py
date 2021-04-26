import sqlalchemy as sa

from lms.db import BASE, TimestampedModelMixin


class HGroup(TimestampedModelMixin, BASE):
    __tablename__ = "h_group"
    __table_args__ = (sa.UniqueConstraint("name", "authority_provided_id"),)

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    name = sa.Column(
        sa.String(),
        nullable=False,
    )
    authority_provided_id = sa.Column(sa.UnicodeText(), nullable=False)

    type = sa.Column(
        sa.String(),
        nullable=False,
    )

    def groupid(self, authority):
        return f"group:{self.authority_provided_id}@{authority}"
