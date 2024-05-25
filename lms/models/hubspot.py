from datetime import date

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base


class HubSpotCompany(Base):
    """Raw companies data imported from HS"""

    __tablename__ = "hubspot_company"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hs_object_id: Mapped[int] = mapped_column(BigInteger, unique=True)

    name: Mapped[str | None]
    lms_organization_id: Mapped[str | None]

    current_deal_services_start: Mapped[date | None]
    current_deal_services_end: Mapped[date | None]


class HubSpotDeal(Base):
    __tablename__ = "hubspot_deal"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hs_object_id: Mapped[int] = mapped_column(BigInteger, unique=True)

    name: Mapped[str | None]

    services_start: Mapped[date | None]
    services_end: Mapped[date | None]


class HubSpotCompanyDeal(Base):
    __tablename__ = "hubspot_company_deal"

    company_id: Mapped[int] = mapped_column(
        ForeignKey("hubspot_company.id", ondelete="cascade"), primary_key=True
    )
    deal_id: Mapped[int] = mapped_column(
        ForeignKey("hubspot_deal.id", ondelete="cascade"), primary_key=True
    )
