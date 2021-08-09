import sqlalchemy as sa

from lms.db import BASE, BulkAction
from lms.models._mixins import CreatedUpdatedMixin


class File(CreatedUpdatedMixin, BASE):
    """A record of files we've seen in LMS's."""

    __tablename__ = "file"
    __table_args__ = (
        sa.UniqueConstraint("application_instance_id", "lms_id", "type", "course_id"),
    )

    # Enable bulk actions
    BULK_CONFIG = BulkAction.Config(
        upsert_index_elements=[
            "application_instance_id",
            "lms_id",
            "type",
            "course_id",
        ],
        upsert_update_elements=["name", "size"],
    )

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)
    """Primary key"""

    application_instance_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("application_instances.id", ondelete="cascade"),
        nullable=False,
    )
    """The ID of this file's application instance."""

    application_instance = sa.orm.relationship(
        "ApplicationInstance", back_populates="files"
    )
    """This file's application instance."""

    type = sa.Column(sa.UnicodeText(), nullable=False)
    """What type of file is this? e.g. 'canvas_file'."""

    lms_id = sa.Column(sa.UnicodeText(), nullable=False)
    """The natural id of the file in the LMS."""

    parent_lms_id = sa.Column(sa.UnicodeText(), nullable=True)
    """Parent ID of the file in the LMS for LMSes that support file/folder hierarchies"""

    course_id = sa.Column(sa.UnicodeText())
    """If the file is associated with a specific course set it here."""

    name = sa.Column(sa.UnicodeText())
    """The user facing file name."""

    size = sa.Column(sa.Integer())
    """The size of the file in bytes."""
