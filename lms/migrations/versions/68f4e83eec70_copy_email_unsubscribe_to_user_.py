"""Copy email_unsubscribe to user_preferences.

Revision ID: 68f4e83eec70
Revises: 6d72ce7efdeb
"""
import logging

from alembic import op
from sqlalchemy import Column, Integer, Unicode, UniqueConstraint, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import declarative_base, sessionmaker

revision = "68f4e83eec70"
down_revision = "6d72ce7efdeb"


Base = declarative_base()
Session = sessionmaker()


log = logging.getLogger(__name__)


class EmailUnsubscribe(Base):
    __tablename__ = "email_unsubscribe"
    id = Column(Integer(), autoincrement=True, primary_key=True)
    h_userid = Column(Unicode, nullable=False)


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, autoincrement=True, primary_key=True)
    h_userid = Column(Unicode, nullable=False, unique=True)
    preferences = Column(
        MutableDict.as_mutable(JSONB),
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )


ALL_DAYS_FALSE = {
    "instructor_email_digests.days.mon": False,
    "instructor_email_digests.days.tue": False,
    "instructor_email_digests.days.wed": False,
    "instructor_email_digests.days.thu": False,
    "instructor_email_digests.days.fri": False,
    "instructor_email_digests.days.sat": False,
    "instructor_email_digests.days.sun": False,
}


def upgrade() -> None:
    session = Session(bind=op.get_bind())

    unsubscribes = session.scalars(select(EmailUnsubscribe)).all()

    log.info("Found %s unsubscribes", len(unsubscribes))

    existing_preferences = session.scalars(
        select(UserPreferences).where(
            UserPreferences.h_userid.in_(
                [unsubscribe.h_userid for unsubscribe in unsubscribes]
            )
        )
    ).all()

    log.info("Found %s existing user_preferences rows", len(existing_preferences))

    updated = 0
    created = 0

    for unsubscribe in unsubscribes:
        for preferences in existing_preferences:
            if preferences.h_userid == unsubscribe.h_userid:
                preferences.preferences.update(ALL_DAYS_FALSE)
                updated += 1
                break
        else:
            session.add(
                UserPreferences(
                    h_userid=unsubscribe.h_userid, preferences=ALL_DAYS_FALSE
                )
            )
            created += 1

    session.commit()

    log.info(
        "Updated %s rows and created %s rows in user_preferences", updated, created
    )


def downgrade() -> None:
    pass
