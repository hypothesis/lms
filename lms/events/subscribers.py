from pyramid.events import subscriber

from lms.events.event import BaseEvent
from lms.services import EventService


@subscriber(BaseEvent)
def handle_event(event: BaseEvent):
    """Record the event in the Event model's table."""
    assert event.request  # noqa: S101
    event.request.find_service(EventService).insert_event(event)
