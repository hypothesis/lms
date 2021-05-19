import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from lms.db import BASE
from lms.models import CreatedUpdatedMixin
from lms.models.application_settings import ApplicationSettings

MAX_GROUP_NAME_LENGTH = 25


class Grouping(CreatedUpdatedMixin, BASE):
    __tablename__ = "grouping"
    __mapper_args__ = {"polymorphic_identity": "grouping", "polymorphic_on": "type"}
    __table_args__ = (
        sa.UniqueConstraint("application_instance_id", "authority_provided_id"),
    )

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    application_instance_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("application_instances.id", ondelete="cascade"),
        nullable=False,
    )
    application_instance = sa.orm.relationship("ApplicationInstance")

    authority_provided_id = sa.Column(sa.UnicodeText(), nullable=False)

    parent_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("grouping.id", ondelete="cascade"),
        nullable=True,
    )

    #: ID on the LMS, not unique across LMS or even in the same LMS instance
    lms_id = sa.Column(sa.String(), nullable=False)

    #: Full name given on the LMS (e.g. "A course name 101")
    lms_name = sa.Column(sa.UnicodeText(), nullable=False)

    type = sa.Column(sa.String(), nullable=False)

    settings = sa.Column(
        "settings",
        ApplicationSettings.as_mutable(JSONB),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )

    extra = sa.Column(
        "extra",
        ApplicationSettings.as_mutable(JSONB),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )

    @property
    def name(self):
        """Return an h-compatible group name."""
        name = self.lms_name.strip()

        if len(name) > MAX_GROUP_NAME_LENGTH:
            return name[: MAX_GROUP_NAME_LENGTH - 1].rstrip() + "…"

        return name

    def groupid(self, authority):
        return f"group:{self.authority_provided_id}@{authority}"


class CanvasSection(Grouping):
    __mapper_args__ = {"polymorphic_identity": "canvas_section"}


class CanvasGroup(Grouping):
    __mapper_args__ = {"polymorphic_identity": "canvas_group"}


class Course(Grouping):
    __mapper_args__ = {"polymorphic_identity": "course"}
