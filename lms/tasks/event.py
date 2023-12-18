from lms.events.event import BaseEvent
from lms.tasks.celery import app


@app.task
def insert_event(event: dict) -> None:
    with app.request_context() as request:  # pylint: disable=no-member
        with request.tm:
            # pylint:disable=import-outside-toplevel,cyclic-import
            from lms.services.event import EventService

            request.find_service(EventService).insert_event(BaseEvent(**event))
