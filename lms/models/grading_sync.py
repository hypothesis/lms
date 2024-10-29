from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms.db import Base, varchar_enum
from lms.models import Assignment
from lms.models._mixins import CreatedUpdatedMixin

if TYPE_CHECKING:
    from lms.models import LMSUser


class AutoGradingSyncStatus(StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    FAILED = "failed"


class GradingSync(CreatedUpdatedMixin, Base):
    __tablename__ = "grading_sync"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignment.id"), index=True)
    assignment: Mapped[Assignment] = relationship()

    status: Mapped[str | None] = varchar_enum(AutoGradingSyncStatus)

    grades: Mapped[list["GradingSyncGrade"]] = relationship(
        "GradingSyncGrade", back_populates="grading_sync"
    )

    created_by_id: Mapped[int] = mapped_column(ForeignKey("lms_user.id"))
    created_by: Mapped["LMSUser"] = relationship()
    """Who created this grade sync."""

    __table_args__ = (
        Index(
            "ix__grading_sync_assignment_status_unique",
            assignment_id,
            unique=True,
            postgresql_where=(status.in_(["scheduled", "in_progress"])),
        ),
        # Only allow one in_progress or scheduled sync per assignment
    )


class GradingSyncGrade(CreatedUpdatedMixin, Base):
    __tablename__ = "grading_sync_grade"

    __table_args__ = (
        UniqueConstraint("grading_sync_id", "lms_user_id"),
        # Only one GradingSyncGrade for the same GradingSync and user""",
    )

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    grading_sync_id: Mapped[int] = mapped_column(
        ForeignKey("grading_sync.id"), index=True
    )
    grading_sync: Mapped[GradingSync] = relationship(
        "GradingSync", back_populates="grades"
    )

    lms_user_id: Mapped[int] = mapped_column(ForeignKey("lms_user.id"), index=True)
    lms_user: Mapped["LMSUser"] = relationship()
    """Who this grade belongs to"""

    grade: Mapped[float] = mapped_column()

    error_details: Mapped[JSONB] = mapped_column(
        JSONB(), server_default=text("'{}'::jsonb"), nullable=False
    )
    """Any extra information about potential errors while syncing this grade to the LMS"""

    success: Mapped[bool | None] = mapped_column()
    """Whether or not this grade has been synced to the LMS"""

    @property
    def status(self) -> AutoGradingSyncStatus:
        if self.success is None:
            return AutoGradingSyncStatus.IN_PROGRESS

        return (
            AutoGradingSyncStatus.FINISHED
            if self.success
            else AutoGradingSyncStatus.FAILED
        )
