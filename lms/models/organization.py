import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin
from lms.models.json_settings import JSONSettings


class Organization(CreatedUpdatedMixin, Base):
    """Model for Organizations comprised of application instances."""

    __tablename__ = "organization"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    public_id: Mapped[str] = mapped_column(sa.TEXT(), unique=True)

    name = sa.Column(sa.UnicodeText(), nullable=True)
    """Human readable name for the organization."""

    enabled: Mapped[bool] = mapped_column(sa.Boolean(), nullable=False, default=True)
    """Is this organization allowed to use LMS?"""

    parent_id: Mapped[int | None] = mapped_column(
        sa.Integer(),
        sa.ForeignKey("organization.id", ondelete="cascade"),
        nullable=True,
    )
    """Optional parent organization."""

    parent = sa.orm.relationship(
        "Organization", back_populates="children", remote_side=[id]
    )

    children = sa.orm.relationship("Organization", back_populates="parent")
    """Get any children of this organization."""

    application_instances = sa.orm.relationship(
        "ApplicationInstance", back_populates="organization"
    )
    """Get any application instances associated with this organization."""

    settings: Mapped[JSONSettings] = mapped_column(
        JSONSettings.as_mutable(JSONB()),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )
    """Arbitrary settings for the organization."""
