import sqlalchemy as sa

from lms.db import BASE
from lms.models._mixins import CreatedUpdatedMixin


class EmailUnsubscribe(CreatedUpdatedMixin, BASE):
    """A list of users not to send certain types of emails to."""

    __tablename__ = "email_unsubscribe"
    __table_args__ = (sa.UniqueConstraint("h_userid", "tag"),)

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    h_userid = sa.Column(sa.Unicode, nullable=False)
    """Which H user unsubscribed from the email"""

    tag = sa.Column(sa.UnicodeText(), nullable=False)
    """Identify the type of email to not receive anymore"""
