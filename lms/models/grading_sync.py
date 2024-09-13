from sqlalchemy.orm import Mapped, mapped_column, relationship
from lms.models._mixins import CreatedUpdatedMixin

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import ForeignKey, text
from enum import StrEnum
from lms.db import Base, varchar_enum
from lms.models import Assignment


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


class GradingSyncGrade(CreatedUpdatedMixin, Base):
    __tablename__ = "grading_sync_grade"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    grading_sync_id: Mapped[int] = mapped_column(
        ForeignKey("grading_sync.id"), index=True
    )
    grading_sync: Mapped[GradingSync] = relationship(backref="grades")

    lms_user_id: Mapped[int] = mapped_column(ForeignKey("lms_user.id"), index=True)
    lms_user: Mapped["LMSUser"] = relationship()

    grade: Mapped[float | None] = mapped_column()

    extra: Mapped[JSONB] = mapped_column(
        JSONB(),
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    success: Mapped[bool | None] = mapped_column()
