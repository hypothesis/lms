import logging

from lms.services import RSAKeyService
from lms.tasks.celery import app

LOG = logging.getLogger(__name__)

TARGET_KEYS = 5


@app.task
def rotate_keys():
    """Periodically (based on h-periodic) rotate RSA keys."""

    with app.request_context() as request:  # pylint: disable=no-member
        if request.registry.settings["disable_key_rotation"]:
            LOG.info("RSA Key rotation is disabled")
            return

        with request.tm:
            # Using a hardcoded value for target keys
            # and relying on the service's defaults for max_age and max_expired_age
            # until we need to configure these per environment.
            request.find_service(RSAKeyService).rotate(target_keys=TARGET_KEYS)
