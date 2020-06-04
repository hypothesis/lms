import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

from lms.db import BASE
from lms.models.application_settings import ApplicationSettings


class Course(BASE):
    """An LTI course."""

    __tablename__ = "course"

    #: The LTI consumer_key (oauth_consumer_key) of the application instance
    #: that these course settings belong to.
    consumer_key = sa.Column(
        sa.String(),
        sa.ForeignKey("application_instances.consumer_key", ondelete="cascade"),
        primary_key=True,
    )

    #: The authority_provided_id that uniquely identifies the course that these
    #: settings belong to.
    authority_provided_id = sa.Column(sa.UnicodeText(), primary_key=True)

    _settings = sa.Column("settings", MutableDict.as_mutable(JSONB), nullable=False)

    @property
    def settings(self):
        """
        Return this course's settings.

        :rtype: models.ApplicationSettings
        """
        return ApplicationSettings(self._settings)
