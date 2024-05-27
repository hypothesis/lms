from datetime import date

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base


class HubSpotCompany(Base):
    """Raw companies data imported from HS."""

    __tablename__ = "hubspot_company"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hs_object_id: Mapped[int] = mapped_column(BigInteger, unique=True)

    name: Mapped[str | None]
    lms_organization_id: Mapped[str | None]

    current_deal_services_start: Mapped[date | None]
    current_deal_services_end: Mapped[date | None]
