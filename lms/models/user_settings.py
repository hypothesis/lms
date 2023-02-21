from sqlalchemy import Boolean, Column, Integer, Unicode

from lms.db import BASE


class UserSettings(BASE):
    __tablename__ = "user_settings"

    id = Column(Integer, autoincrement=True, primary_key=True)
    h_userid = Column(Unicode, nullable=False, unique=True)
    instructor_email_digests = Column(Boolean())
