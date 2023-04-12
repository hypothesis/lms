from enum import Enum

import sqlalchemy as sa

from lms.db import BASE, varchar_enum
from lms.models._mixins import CreatedUpdatedMixin


class EmailUnsubscribe(CreatedUpdatedMixin, BASE):
    """Store a denylist of for transactional emails."""

    class Tag(str, Enum):
        INSTRUCTOR_DIGEST = "instructor_digest"

    __tablename__ = "email_unsubscribe"
    __table_args__ = (sa.UniqueConstraint("h_userid", "tag"),)

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    h_userid = sa.Column(sa.Unicode, nullable=False)
    """Which H user unsubscribed from the email"""

    tag = varchar_enum(Tag, nullable=False)
    """Identify the type of email to not receive anymore"""
