from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class LMSTerm(CreatedUpdatedMixin, Base):
    __tablename__ = "lms_term"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    tool_consumer_instance_guid: Mapped[str | None] = mapped_column(index=True)

    name: Mapped[str | None] = mapped_column()

    starts_at: Mapped[datetime | None] = mapped_column()
    """The start date of the term."""

    ends_at: Mapped[datetime | None] = mapped_column()
    """The end date of the term."""

    key: Mapped[str] = mapped_column(index=True, unique=True)
    """Not all installs will send us an ID so we'll mantaint an internal key to be able to idneitfy each term and avoid duplicates."""

    lms_id: Mapped[str | None] = mapped_column(index=True)
    """ID of this term on the LMS."""
