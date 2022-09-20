from base64 import urlsafe_b64encode
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from lms.db import BASE
from lms.models._mixins import CreatedUpdatedMixin, PublicIdMixin
from lms.models.application_settings import ApplicationSettings
from lms.models.region import Region


class Organization(CreatedUpdatedMixin, PublicIdMixin, BASE):
    """Model for Organizations comprised of application instances."""

    __tablename__ = "organization"

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    name = sa.Column(sa.UnicodeText(), nullable=True)
    """Human readable name for the organization."""

    enabled = sa.Column(sa.Boolean(), nullable=False, default=True)
    """Is this organization allowed to use LMS?"""

    public_id_model_code = "org"
    """Set the code for the PublicIdMixin which provides `public_id()` etc."""

    parent_id = sa.Column(
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

    settings = sa.Column(
        "settings",
        ApplicationSettings.as_mutable(JSONB),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )
    """Arbitrary settings for the organization."""
