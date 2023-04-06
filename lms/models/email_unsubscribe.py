import sqlalchemy as sa

from lms.db import BASE
from lms.models._mixins import CreatedUpdatedMixin


class EmailUnsubscribe(CreatedUpdatedMixin, BASE):
    """Store a denylist of for transactional emails."""

    __tablename__ = "email_unsubscribe"
    __table_args__ = (sa.UniqueConstraint("email", "tag"),)

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    email = sa.Column(sa.Unicode, nullable=False)
    """To which email address we won't be sending more of this type of email"""

    tag = sa.Column(sa.UnicodeText(), nullable=False)
    """Identify the type of email to not receive anymore"""
