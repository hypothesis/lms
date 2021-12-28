"""Celery app and configuration."""

import logging
import os
import sys
from contextlib import contextmanager

import celery.signals
from celery import Celery
from kombu import Exchange, Queue
from pyramid.scripting import prepare

from lms.app import create_app

LOG = logging.getLogger(__name__)


app = Celery("lms")
app.conf.update(
    # Without some kind of default here we can't even import the module
    # in the tests
    broker_url=os.environ.get(
        "CELERY_BROKER_URL", "amqp://guest:guest@localhost:5674//"
    ),
    # What options should we have when sending messages to the queue?
    broker_transport_options={
        "max_retries": 2,
        # The delay until the first retry
        "interval_start": 0.2,
        # How many seconds added to the interval for each retry
        "interval_step": 0.2,
        # Maximum number of seconds to sleep between each retry
        "interval_max": 0.6,
    },
    # Tell celery where our tasks are defined
    imports=("lms.tasks",),
    # Acknowledge tasks after the task has executed, rather than just before
    task_acks_late=True,
    # Don't store any results, we only use this for scheduling
    task_ignore_result=True,
    task_queues=[
        Queue(
            "celery",
            # We don't care if the messages are lost if the broker restarts
            durable=False,
            routing_key="celery",
            exchange=Exchange("celery", type="direct", durable=False),
        ),
    ],
    # Only accept one task at a time rather than pulling lots off the queue
    # ahead of time. This lets other workers have a go if we fail
    worker_prefetch_multiplier=1,
    worker_disable_rate_limits=True,
)


@celery.signals.worker_init.connect
def bootstrap_worker(sender, **_kwargs):  # pragma: no cover
    """Set up the celery worker with one-time initialisation."""

    # Put some common handy things around for tasks
    try:
        lms = create_app(None, **{})

    except Exception:  # pylint: disable=broad-except
        # If we don't bail out here ourselves, Celery just hides the error
        # and continues. This means `request_context` will not be available
        # when attempting to run tasks, which is impossible to debug.
        LOG.critical("CELERY WORKER DID NOT START: Could not create app", exc_info=True)
        sys.exit(1)

    @contextmanager
    def request_context():
        with prepare(registry=lms.registry) as env:
            yield env["request"]

    sender.app.request_context = request_context


@celery.signals.task_prerun.connect
def add_task_name_and_id_to_log_messages(
    task_id, task, *_args, **_kwargs
):  # pragma: no cover
    """Add the Celery task name and ID to all messages logged by Celery tasks.

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
