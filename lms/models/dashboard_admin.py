import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin
from lms.models.organization import Organization


class DashboardAdmin(CreatedUpdatedMixin, Base):
    """LMS users that are given full admin access to the dashboards."""

    __tablename__ = "dashboard_admin"
    __table_args__ = (sa.UniqueConstraint("organization_id", "email"),)

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    created_by: Mapped[str] = mapped_column(nullable=False)

    email: Mapped[str] = mapped_column(nullable=False)
    """Email of the LMS user that have admin access to `organization`.

    We don't use user_id or h_userid to allow:

        - Easier comunication with LMS admins
        - The possiblity of adding a user without a previous launch.
    """

    organization_id: Mapped[int] = mapped_column(
        sa.ForeignKey("organization.id", ondelete="cascade"), nullable=False
    )

    organization: Mapped[Organization] = sa.orm.relationship(
        "Organization", backref=sa.orm.backref("dashboard_admins")
    )
