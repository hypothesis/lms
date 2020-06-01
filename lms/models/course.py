import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm.exc import NoResultFound

from lms.db import BASE
from lms.models.application_settings import ApplicationSettings


class Course(BASE):
    """An LTI course."""

    __tablename__ = "course"

    #: The authority_provided_id that uniquely identifies the course that these
    #: settings belong to.
    authority_provided_id = sa.Column(sa.UnicodeText(), primary_key=True)

    #: The LTI consumer_key (oauth_consumer_key) of the application instance
    #: that these course settings belong to.
    consumer_key = sa.Column(
        sa.String(),
        sa.ForeignKey("application_instances.consumer_key", ondelete="cascade"),
        primary_key=True,
    )

    _settings = sa.Column("settings", MutableDict.as_mutable(JSONB), nullable=False)

    @property
    def settings(self):
        """
        Return this course's settings.

        :rtype: models.ApplicationSettings
        """
        return ApplicationSettings(self._settings)

    @classmethod
    def get(cls, db, authority_provided_id, consumer_key):
        """Return the course matching `authority_provided_id` and `consumer_key` or None."""
        try:
            return cls._get(db, authority_provided_id, consumer_key)
        except NoResultFound:
            return None

    @classmethod
    def insert_if_not_exists(cls, db, authority_provided_id, consumer_key, settings):
        """
        Insert the given settings into the DB if none already exist.

        If there's no existing row with the `authority_provided_id` and
        `consumer_key` then insert the `settings` into the course table with
        `authority_provided_id` and `consumer_key`.

        If a row matching `authority_provided_id` and `consumer_key` already
        exists then do nothing.
        """
        course = cls(
            authority_provided_id=authority_provided_id,
            consumer_key=consumer_key,
            _settings=settings,
        )

        try:
            cls._get(db, authority_provided_id, consumer_key)
        except NoResultFound:
            db.add(course)

    @classmethod
    def _get(cls, db, authority_provided_id, consumer_key):
        return (
            db.query(cls)
            .filter_by(
                authority_provided_id=authority_provided_id, consumer_key=consumer_key,
            )
            .one()
        )
