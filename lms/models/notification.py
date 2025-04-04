import enum

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lms.db import Base, varchar_enum
from lms.models._mixins import CreatedUpdatedMixin
from lms.models.lms_user import LMSUser


class Notification(CreatedUpdatedMixin, Base):
    """Keep track of sent notifications.

    Allows us both to report on the number of notifications sent and to
    ensure that a user doesn't receive multiple notifications for the same event.
    """

    class Type(enum.StrEnum):
        REPLY = "REPLY"
        MENTION = "MENTION"

    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    notification_type: Mapped[Type] = varchar_enum(Type)

    source_annotation_id: Mapped[str] = mapped_column()

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("lms_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """FK to LMSUser.id - the user that generated the notification, the author of the annotation"""
    sender: Mapped[LMSUser] = relationship(
        "LMSUser", uselist=False, foreign_keys=[sender_id]
    )

    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("lms_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    """FK to LMSUser.id - the user receiving the notification"""
    recipient: Mapped[LMSUser] = relationship(
        "LMSUser", uselist=False, foreign_keys=[recipient_id]
    )

    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignment.id", ondelete="cascade")
    )
    assignment = relationship("Assignment")
    """Assignment that the notification is related to"""

    __table_args__ = (
        # Ensure that a recipient can only have one notification for a given source annotation
        UniqueConstraint(
            "recipient_id",
            "source_annotation_id",
            name="uq__notification__recipient_id__source_annotation_id",
        ),
    )
