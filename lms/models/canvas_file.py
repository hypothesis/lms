import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList

from lms.db import BASE


class CanvasFile(BASE):
    """
    A file that we've seen in a response from the Canvas Files API.

    https://canvas.instructure.com/doc/api/files.html
    """

    __tablename__ = "canvas_file"
    __table_args__ = (
        sa.UniqueConstraint("consumer_key", "tool_consumer_instance_guid", "file_id"),
    )

    id = sa.Column(sa.Integer, primary_key=True)

    consumer_key = sa.Column(
        sa.String,
        sa.ForeignKey("application_instances.consumer_key", ondelete="cascade"),
        nullable=False,
    )
    tool_consumer_instance_guid = sa.Column(sa.UnicodeText, nullable=False)
    file_id = sa.Column(sa.Integer, nullable=False)

    course_id = sa.Column(sa.Integer, nullable=False)
    filename = sa.Column(sa.UnicodeText, nullable=False)
    size = sa.Column(sa.Integer, nullable=False)

    # The file_id's of other Canvas files, in other courses, that we know this
    # file was directly or indirectly copied from.
    file_id_history = sa.Column(
        MutableList.as_mutable(ARRAY(sa.Integer)),
        server_default="{}",
        nullable=False,
    )

    application_instance = sa.orm.relationship(
        "ApplicationInstance", back_populates="canvas_files"
    )
