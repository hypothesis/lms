import logging

from lms.tasks.celery import app

LOG = logging.getLogger(__name__)


@app.task
def annotation_event(*, event) -> None:  # noqa: ARG001
    """
    Process annotations events.

    These are published directly on LMS's queue by H
    """
    # For now we are just consuming the messages to keep the queue clean while
    # we deploy the publishing side on H.
    return
