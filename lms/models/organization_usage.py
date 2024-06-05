from datetime import date

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin
from lms.models.organization import Organization


class OrganizationUsageReport(CreatedUpdatedMixin, Base):
    __tablename__ = "organization_usage_report"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organization.id", ondelete="cascade")
    )
    organization: Mapped[Organization] = relationship(backref="reports")

    tag: Mapped[str] = mapped_column()

    key: Mapped[str] = mapped_column(unique=True)
    """Key that idenfities this report"""

    since: Mapped[date | None]
    until: Mapped[date | None]

    unique_users: Mapped[int | None] = mapped_column()

    report: Mapped[list[dict] | None] = mapped_column(JSONB())
    """Actual report, in JSON format."""

    @classmethod
    def generate_key(cls, organization, tag: str, report_start: date, report_end: date):
        return f"{organization.public_id}-{tag}-{report_start}-{report_end}"
