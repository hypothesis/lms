from sqlalchemy import Column, DateTime, Integer, UnicodeText, text
from sqlalchemy.dialects.postgresql import JSONB

from lms.db import BASE
from lms.models._mixins import CreatedUpdatedMixin


class TaskDone(CreatedUpdatedMixin, BASE):
    __tablename__ = "task_done"

    id = Column(Integer, autoincrement=True, primary_key=True)
    key = Column(UnicodeText, nullable=False, unique=True)
    data = Column(JSONB, server_default=text("'{}'::jsonb"), nullable=True)
    expires_at = Column(
        DateTime, nullable=False, server_default=text("now() + interval '30 days'")
    )
