"""Celery app and configuration."""

import logging
import os
import sys
from contextlib import contextmanager

import celery.signals
from celery import Celery
from pyramid.scripting import prepare

from lms.app import create_app

LOG = logging.getLogger(__name__)


app = Celery("lms")
app.conf.update(
    broker_url=os.environ.get("BROKER_URL"),
    broker_transport_options={
        # Celery's docs are very unclear about this but: when publishing a
        # message to RabbitMQ these options end up getting passed to Kombu's
        # _ensure_connection() function:
        # https://github.com/celery/kombu/blob/3e098dc94ed2a389276ccf3606a0ded3da157d72/kombu/connection.py#L399-L453
        #
        # By default _ensure_connection() can spend over 6s trying to establish
        # a connection to RabbitMQ if RabbitMQ is down. This means that if
        # RabbitMQ goes down then all of our web processes can quickly become
        # occupied trying to establish connections when web requests try to
        # call Celery tasks with .delay() or .apply_async().
        #
        # These options change it to use a smaller number of retries and less
        # time between retries so that attempts fail fast when RabbitMQ is down
        # and our whole web app remains responsive.
        #
        # For more info see: https://github.com/celery/celery/issues/4627#issuecomment-396907957
        "max_retries": 2,
        "interval_start": 0.2,
        "interval_step": 0.2,
    },
    # Tell Celery to kill any task run (by raising
    # celery.exceptions.SoftTimeLimitExceeded) if it takes longer than
    # task_soft_time_limit seconds.
    #
    # See: https://docs.celeryq.dev/en/stable/userguide/workers.html#time-limits
    #
    # This is to protect against task runs hanging forever which blocks a
    # Celery worker and prevents Celery retries from kicking in.
    #
    # This can be overridden on a per-task basis by adding soft_time_limit=n to
    # the task's @app.task() arguments.
    #
    # We're using soft rather than hard time limits because hard time limits
    # don't trigger Celery retries whereas soft ones do. Soft time limits also
    # give the task a chance to catch SoftTimeLimitExceeded and do some cleanup
    # before exiting.
    task_soft_time_limit=120,
    # Tell Celery to force-terminate any task run (by terminating the worker
    # process and replacing it with a new one) if it takes linger than
    # task_time_limit seconds.
    #
    # This is needed to defend against tasks hanging during cleanup: if
    # task_soft_time_limit expires the task can catch SoftTimeLimitExceeded and
    # could then hang again in the exception handler block. task_time_limit
    # ensures that the task is force-terminated in that case.
    #
    # This can be overridden on a per-task basis by adding time_limit=n to the
    # task's @app.task() arguments.
    task_time_limit=240,
    # Disable Celery task rate limits in local development.
    worker_disable_rate_limits=os.environ.get("DEV") == "true",
    # Tell celery where our tasks are defined
    imports=("lms.tasks",),
)


@celery.signals.worker_init.connect
def bootstrap_worker(sender, **_kwargs):  # pragma: no cover
    """Set up the celery worker with one-time initialisation."""

    # Put some common handy things around for tasks
    try:
        lms = create_app(None, **{})

    except Exception:  # noqa: BLE001
        # If we don't bail out here ourselves, Celery just hides the error
        # and continues. This means `request_context` will not be available
        # when attempting to run tasks, which is impossible to debug.
        LOG.critical("CELERY WORKER DID NOT START: Could not create app", exc_info=True)
        sys.exit(1)

    @contextmanager
    def request_context():
        with prepare(registry=lms.registry) as env:
            request = env["request"]

            # Make Pyramid things like route_url() and static_url() use the
            # right hostname and port when called by Celery tasks.
            request.environ["HTTP_HOST"] = os.environ["HTTP_HOST"]

            yield request

    sender.app.request_context = request_context


@celery.signals.task_prerun.connect
def add_task_name_and_id_to_log_messages(
    task_id, task, *_args, **_kwargs
):  # pragma: no cover
    """
    Add the Celery task name and ID to all messages logged by Celery tasks.

    This makes it easier to observe Celery tasks by reading the logs. For
    example you can find all messages logged by a given Celery task by
    searching for the task's name in the logs.

    This affects:

    * Logging by Celery itself
    * Logging in our Celery task functions or anything they call (directly or
      indirectly)

    """
    # Replace the root logger's formatter with one that includes task.name and
    # task_id in the format. This assumes that the root logger has one handler,
    # which happens to be the case.
    root_loggers_handler = logging.getLogger().handlers[0]

    root_loggers_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s: %(levelname)s/%(processName)s] "
            + f"{task.name}[{task_id}] "
            + "%(message)s"
        )
    )
