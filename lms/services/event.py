from functools import lru_cache

from sqlalchemy.orm import Session

from lms.events.event import BaseEvent
from lms.models import Event, EventData, EventType, EventUser


class EventService:
    def __init__(self, db: Session):
        self._db = db

    def insert_event(self, event: BaseEvent):
        """
        Insert an event into the DB.

        Takes a `BaseEvent` and inserts a new row in the `events` table.
        """
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

        return event

    @lru_cache(maxsize=10)
    def _get_type_pk(self, type_: EventType.Type) -> int:
        """Cache the PK of the event_type table to avoid an extra query while inserting events."""
        event_type = self._db.query(EventType).filter_by(type=type_).one_or_none()
        if not event_type:
            event_type = EventType(type=type_)
            self._db.add(event_type)
            self._db.flush()

        return event_type.id

    @classmethod
    def from_db_session(cls, db):
        return cls(db)


def factory(_context, request):
    return EventService.from_db_session(db=request.db)
