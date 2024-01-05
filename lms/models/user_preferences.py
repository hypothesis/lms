from sqlalchemy import Column, Integer, Unicode, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class UserPreferences(CreatedUpdatedMixin, Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, autoincrement=True, primary_key=True)
    h_userid = Column(Unicode, nullable=False, unique=True)
    preferences = Column(
        MutableDict.as_mutable(JSONB),
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
