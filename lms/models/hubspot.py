from datetime import date

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from lms.db import Base
from lms.models.organization import Organization


class HubSpotCompany(Base):
    """Raw companies data imported from HS."""

    __tablename__ = "hubspot_company"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hubspot_id: Mapped[int] = mapped_column(BigInteger, unique=True)

    name: Mapped[str | None]

    lms_organization_id: Mapped[str | None]
    current_deal_services_start: Mapped[date | None]
    current_deal_services_end: Mapped[date | None]
    current_deal_users_contracted: Mapped[int | None]

    student_fte: Mapped[int | None]
    """Full-time equivalent students, as entered in HubSpot."""

    contract_type: Mapped[str | None]
    """School, System, Unlimited, Department, Course or Student Pay."""

    parent_hubspot_id: Mapped[int | None] = mapped_column(BigInteger)
    """HubSpot ID of the parent company, if this company has one."""

    organization: Mapped[Organization] = relationship(
        "Organization",
        primaryjoin=lambda: foreign(Organization.public_id)
        == HubSpotCompany.lms_organization_id,
    )
