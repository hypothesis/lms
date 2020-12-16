from sqlalchemy import Column, UnicodeText, String, Integer

from lms.db import BASE


class CanvasFile(BASE):
    __tablename__ = "canvas_file"

    id = Column(Integer, autoincrement=True, primary_key=True)

    consumer_key = Column(String)
    tool_consumer_instance_guid = Column(UnicodeText)

    # The course ID (the context_id launch param).
    course_id = Column(UnicodeText)

    # Metadata about the file, from the Canvas API.
    filename = Column(UnicodeText)
    size = Column(UnicodeText)
    file_id = Column(Integer)
    file_id_override = Column(UnicodeText)
