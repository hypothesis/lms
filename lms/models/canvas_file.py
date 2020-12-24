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
    file_id = sa.Column(sa.Integer, nullable=False)
    course_id = sa.Column(sa.Integer, nullable=False)

    application_instance = sa.orm.relationship(
        "ApplicationInstance", back_populates="canvas_files"
    )

    type = sa.Column(sa.UnicodeText, nullable=False)

    __mapper_args__ = {
        "polymorphic_on": type,
    }


class CanvasFile(CanvasFileBase):
    filename = sa.Column(sa.UnicodeText)
    size = sa.Column(sa.Integer)
    overrides = sa.orm.relationship(
        "CanvasFileOverride",
        backref=sa.orm.backref("canvas_file", remote_side=["id"]),
    )

    __mapper_args__ = {"polymorphic_identity": "CanvasFile"}


class CanvasFileOverride(CanvasFileBase):
    file_id_override = sa.Column(sa.Integer, ForeignKey("CanvasFile.file_id"))

    __mapper_args__ = {"polymorphic_identity": "CanvasFileOverride"}
