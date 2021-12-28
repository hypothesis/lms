from celery.utils.log import get_task_logger

from lms.tasks.celery import app
from lms.models import BlackboardGroup
import time


LOG = get_task_logger(__name__)


@app.task
def get_groups():
    with app.request_context() as request:
        with request.tm:
            groups = request.db.query(BlackboardGroup).limit(5).all()
            authority = request.registry.settings["h_authority"]
            time.sleep(10)
            return [group.groupid(authority) for group in groups]
