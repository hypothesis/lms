from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ForeignKey

from lms.db import Base
from datetime import date


class HubSpotCompaniesRaw(Base):
    """Raw companies data imported from HS"""

    __tablename__ = "hubspot_companies_raw"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str | None]
    lms_organization_id: Mapped[str | None]
    life_cycle_stage: Mapped[str | None]

    # Owners
    company_owner_id: Mapped[int | None]
    success_owner_id: Mapped[int | None]

    # Cohort
    cohort_pilot_first_date: Mapped[date | None]
    cohort_subscription_first_date: Mapped[date | None]

    # Deals
    current_deal_services_start: Mapped[date | None]
    current_deal_services_end: Mapped[date | None]
    current_deal_amount: Mapped[float | None]
    deals_last_update: Mapped[date | None]


class HubSpotDeal(Base):
    """Raw companies data imported from HS"""

    __tablename__ = "hubspot_deals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str | None]

    services_start: Mapped[date | None]
    services_end: Mapped[date | None]

    amount: Mapped[float | None]

    company_id: Mapped[int] = mapped_column(
        ForeignKey("hubspot_companies_raw.id", ondelete="cascade")
    )
