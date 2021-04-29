import sqlalchemy as sa

from lms.db import BASE, TimestampedModelMixin

MAX_GROUP_NAME_LENGTH = 25


class HGroup(TimestampedModelMixin, BASE):
    __tablename__ = "h_group"
    __table_args__ = (sa.UniqueConstraint("authority_provided_id"),)

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    # Full name of the group in the LMS
    _name = sa.Column(
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

    @property
    def name(self):
        """Return an h-compatible group name from the given string."""

        name = self._name.strip()

        if len(name) > MAX_GROUP_NAME_LENGTH:
            return name[: MAX_GROUP_NAME_LENGTH - 1].rstrip() + "…"

        return name
