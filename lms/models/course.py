import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from lms.db import BASE
from lms.models.application_settings import ApplicationSettings
from lms.models.grouping import Grouping


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

    #: The ApplicationInstance that this access token belongs to.
    application_instance = sa.orm.relationship(
        "ApplicationInstance", back_populates="courses"
    )

    #: The authority_provided_id that uniquely identifies the course that these
    #: settings belong to.
    authority_provided_id = sa.Column(sa.UnicodeText(), primary_key=True)

    settings = sa.Column(
        "settings",
        ApplicationSettings.as_mutable(JSONB),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )


class _Course(Grouping):
    __tablename__ = "course_grouping"
    __mapper_args__ = {"polymorphic_identity": "course"}

    id = sa.Column(sa.Integer, sa.ForeignKey("grouping.id"), primary_key=True)

    settings = sa.Column(
        "settings",
        ApplicationSettings.as_mutable(JSONB),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )
