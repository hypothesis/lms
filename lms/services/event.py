from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from lms.models import Event, EventData, EventType, EventUser

if TYPE_CHECKING:
    from lms.events import BaseEvent


class EventService:
    def __init__(self, db: Session):
        self._db = db

    def insert_event(self, event: BaseEvent):

        db_event = Event(
            type_id=self._get_type_pk(event.type),
            application_instance_id=event.application_instance_id,
            course_id=event.course_id,
            assignment_id=event.assignment_id,
            grouping_id=event.grouping_id,
        )
        self._db.add(db_event)

        if event.user_id:
            for role_id in event.role_ids or [None]:
                self._db.add(
                    EventUser(
                        event=db_event, user_id=event.user_id, lti_role_id=role_id
                    )
                )

        if event.data:
            self._db.add(EventData(event=db_event, data=event.data))

    @lru_cache
    def _get_type_pk(self, type_: EventType.Type) -> int:
        return self._db.query(EventType).filter_by(type=type_).one().id


def factory(_context, request):
    return EventService(request.db)
