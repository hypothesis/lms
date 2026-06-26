from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class AssignmentCheckpoint(CreatedUpdatedMixin, Base):
    """Hide & Reveal configuration for an assignment.

    The existence of a row marks the assignment as a Hide & Reveal assignment
    (mirroring how a NULL auto_grading_config_id marks a non-auto-graded one).

    Reveal is whole-assignment: a single reveal_date applies to every group the
    assignment is launched into. This LMS-side row is the source of truth for
    that reveal state; on each launch the LMS fans it out into one h checkpoint
    per (group, document) for server-side authorization. The LMS must persist
    reveal_date here because lti_h.sync blindly re-sends current data on every
    launch, so without it a re-sync would overwrite h's reveal_date back to NULL
    and un-reveal an already-revealed assignment.
    """

    __tablename__ = "assignment_checkpoint"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    assignment_id: Mapped[int] = mapped_column(
        sa.ForeignKey("assignment.id", ondelete="cascade"), index=True
    )
    assignment = relationship("Assignment", back_populates="checkpoint")

    reveal_date: Mapped[datetime | None] = mapped_column()
    """When the instructor revealed the assignment; NULL until revealed."""
