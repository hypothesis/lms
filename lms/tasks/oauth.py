from celery.utils.log import get_task_logger

from lms.tasks.celery import app
from lms.models import OAuth2Token

LOG = get_task_logger(__name__)


@app.task
def refresh_tokens():
    # pylint: disable=no-member
    with app.request_context() as request:
        with request.tm:
            count = request.db.query(OAuth2Token).count()
            LOG.info("Found %d tokens", count)
