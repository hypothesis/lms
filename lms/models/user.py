import sqlalchemy as sa

from lms.db import BASE
from lms.models import CreatedUpdatedMixin


class User(CreatedUpdatedMixin, BASE):
    """A user record to link between LTI users and H users."""

    __tablename__ = "user"
    __table_args__ = (
        sa.UniqueConstraint(
            "application_instance_id",
            "user_id",
            name="uq__user__application_instance_id__user_id",
        ),
        sa.UniqueConstraint(
            "application_instance_id",
            "h_userid",
            name="uq__user__application_instance_id__h_userid",
        ),
    )

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    """An arbitrary primary id."""

    application_instance_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("application_instances.id", ondelete="cascade"),
        nullable=False,
    )
    application_instance = sa.orm.relationship("ApplicationInstance")

    user_id = sa.Column(sa.Unicode, nullable=False)
    """The user id provided by the LTI parameters."""

    roles = sa.Column(sa.Unicode, nullable=True)
    """The roles provided by the LTI parameters."""

    h_userid = sa.Column(sa.Unicode, nullable=False)
    """The H userid which is created from LTI provided values."""
