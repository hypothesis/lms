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

    application_instance = sa.orm.relationship(
        "ApplicationInstance", back_populates="canvas_files"
    )
    lookups = sa.orm.relationship("CanvasFileLookup", back_populates="canvas_file")


class CanvasFileLookup(BASE):
    """A table for looking up rows in the canvas_file table above."""

    __tablename__ = "canvas_file_lookup"
    __table_args__ = (
        sa.UniqueConstraint(
            "consumer_key", "tool_consumer_instance_guid", "course_id", "file_id"
        ),
    )

    id = sa.Column(sa.Integer, primary_key=True)

    consumer_key = sa.Column(
        sa.String,
        sa.ForeignKey("application_instances.consumer_key", ondelete="cascade"),
        nullable=False,
    )
    tool_consumer_instance_guid = sa.Column(sa.UnicodeText, nullable=False)
    course_id = sa.Column(sa.Integer, nullable=False)
    file_id = sa.Column(sa.Integer, nullable=False)

    canvas_file_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("application_instances.consumer_key", ondelete="cascade"),
        nullable=False,
    )

    application_instance = sa.orm.relationship(
        "ApplicationInstance", back_populates="canvas_files"
    )
    canvas_file = sa.orm.relationship("CanvasFile", back_populates="lookups")
