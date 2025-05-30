from collections.abc import Mapping
from enum import Enum, StrEnum

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin
from lms.models.json_settings import JSONSetting, JSONSettings


class OrganizationSettings(JSONSettings):
    class Settings(StrEnum, Enum):
        HYPOTHESIS_NOTES = "hypothesis.notes"

    fields: Mapping[Settings, JSONSetting] = {
        Settings.HYPOTHESIS_NOTES: JSONSetting(Settings.HYPOTHESIS_NOTES),
    }


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

    children = sa.orm.relationship(
        "Organization", backref=sa.orm.backref("parent", remote_side=[id])
    )
    """Get any children of this organization."""

    application_instances = sa.orm.relationship(
        "ApplicationInstance", back_populates="organization"
    )
    """Get any application instances associated with this organization."""

    settings: Mapped[OrganizationSettings] = mapped_column(
        OrganizationSettings.as_mutable(JSONB()),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )
    """Arbitrary settings for the organization."""
