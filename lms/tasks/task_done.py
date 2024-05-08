"""Celery tasks for maintaining the task_done database table."""

from datetime import datetime

from sqlalchemy import delete

from lms.models import TaskDone
from lms.tasks.celery import app


@app.task
def delete_expired_rows():
    """
    Delete any expired rows from the task_done table.

    This is just so that the table doesn't grow forever.

    This is intended to be called periodically.
    """
    with app.request_context() as request:
        with request.tm:
            request.db.execute(
                delete(TaskDone).where(TaskDone.expires_at < datetime.utcnow())
            )
