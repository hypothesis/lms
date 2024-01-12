from base64 import urlsafe_b64encode
from os import environ
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from lms.db import BASE
from lms.models._mixins import CreatedUpdatedMixin
from lms.models.json_settings import JSONSettings


def _generate_public_id() -> str:
    return urlsafe_b64encode(uuid4().bytes).decode("ascii").rstrip("=")


class InvalidOrganizationPublicId(Exception):
    pass


class Organization(CreatedUpdatedMixin, BASE):
    """Model for Organizations comprised of application instances."""

    __tablename__ = "organization"

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    name = sa.Column(sa.UnicodeText(), nullable=True)
    """Human readable name for the organization."""

    enabled = sa.Column(sa.Boolean(), nullable=False, default=True)
    """Is this organization allowed to use LMS?"""

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
        JSONSettings.as_mutable(JSONB),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )
    """Arbitrary settings for the organization."""

    _public_id = sa.Column(
        "public_id",
        sa.UnicodeText(),
        nullable=False,
        unique=True,
        default=_generate_public_id,
    )

    @property
    def public_id(self):
        return f"{environ['REGION_CODE']}.lms.org.{self._public_id}"

    @staticmethod
    def remove_prefix(public_id):
        try:
            return public_id.split(".")[3]
        except IndexError as err:
            raise InvalidOrganizationPublicId(
                f"Malformed public id: '{public_id}'. Expected 4 dot separated parts."
            ) from err
