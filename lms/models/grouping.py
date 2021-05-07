import sqlalchemy as sa

from lms.db import BASE


class Grouping(BASE):
    __tablename__ = "grouping"
    __mapper_args__ = {"polymorphic_identity": "grouping", "polymorphic_on": "type"}
    __table_args__ = (
        sa.UniqueConstraint("application_instance_id", "authority_provided_id"),
    )

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    application_instance_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("application_instances.id", ondelete="cascade"),
    )
    authority_provided_id = sa.Column(sa.UnicodeText())
    type = sa.Column(sa.String())

    name = sa.Column(sa.UnicodeText(), nullable=False)


class CanvasSection(Grouping):
    __mapper_args__ = {"polymorphic_identity": "canvas_section"}


class CanvasGroup(Grouping):
    __mapper_args__ = {"polymorphic_identity": "canvas_group"}
