import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from lms.events.event import BaseEvent
from lms.models import Event, EventData
from lms.tasks.celery import app

LOG = logging.getLogger(__name__)


PURGE_LAUNCH_DATA_BATCH_SIZE = 1000
"How many rows to remove per call to purge_launch_data"


@app.task
def insert_event(event: dict) -> None:
    with app.request_context() as request:
        with request.tm:
            from lms.services.event import EventService  # noqa: PLC0415

            request.find_service(EventService).insert_event(
                BaseEvent(request=request, **event)
            )


@app.task
def purge_launch_data(*, max_age_days=30) -> None:
    with app.request_context() as request:
        with request.tm:
            events_with_old_lti_params = (
                select(Event.id)
                .join(EventData)
                .where(
                    # Find data that's is at least max_age_days old
                    Event.timestamp <= datetime.now(UTC) - timedelta(days=max_age_days),
                    # Limit the search for only twice as old as we'd expect, limiting the data set significally
                    Event.timestamp
                    >= datetime.now(UTC) - timedelta(days=max_age_days * 2),
                    EventData.data["lti_params"].is_not(None),
                )
                .limit(PURGE_LAUNCH_DATA_BATCH_SIZE)
            )
            results = request.db.execute(
                update(EventData)
                .where(EventData.event_id.in_(events_with_old_lti_params))
                .values(data=EventData.data - "lti_params")
            )
            LOG.info("Removed lti_params from events for %d rows", results.rowcount)
