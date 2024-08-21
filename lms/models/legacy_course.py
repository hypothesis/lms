import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base
from lms.models.json_settings import JSONSettings


class LegacyCourse(Base):
    """An LTI course."""

    __tablename__ = "course"

    #: The LTI consumer_key (oauth_consumer_key) of the application instance
    #: that these course settings belong to.
    consumer_key = sa.Column(
        sa.Unicode(),
        sa.ForeignKey("application_instances.consumer_key", ondelete="cascade"),
        primary_key=True,
    )

    #: The authority_provided_id that uniquely identifies the course that these
    #: settings belong to.
    authority_provided_id = sa.Column(sa.UnicodeText(), primary_key=True)

    settings: Mapped[JSONSettings] = mapped_column(
        JSONSettings.as_mutable(JSONB()),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )
