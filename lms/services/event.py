from functools import lru_cache

from sqlalchemy.orm import Session

from lms.models import Event, EventData, EventType, EventUser


class EventService:
    def __init__(self, db: Session):
        self._db = db

    def insert_event(
        self, type_: EventType, user: None, lti_roles=None, data=None, **kwargs
    ):

        event = Event(type_id=self._get_type_pk(type_), **kwargs)
        self._db.add(event)

        if user:
            for lti_role in lti_roles or [None]:
                self._db.add(EventUser(event=event, user=user, lti_role=lti_role))

        if data:
            self._db.add(EventData(event=event, data=data))

    @lru_cache
    def _get_type_pk(self, type_: EventType.Type) -> int:
        return self._db.query(EventType).filter_by(type=type_).one().id


def factory(_context, request):
    return EventService(request.db)
