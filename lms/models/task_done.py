from sqlalchemy import Column, DateTime, Integer, UnicodeText, text
from sqlalchemy.dialects.postgresql import JSONB

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class TaskDone(CreatedUpdatedMixin, Base):
    __tablename__ = "task_done"

    id = Column(Integer, autoincrement=True, primary_key=True)
    key = Column(UnicodeText, nullable=False, unique=True)
    expires_at = Column(
        DateTime, nullable=False, server_default=text("now() + interval '30 days'")
    )
    data = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
