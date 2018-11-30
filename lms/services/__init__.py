from lms.services.exceptions import HAPIError
from lms.services.exceptions import HAPINotFoundError

__all__ = ("HAPIError", "HAPINotFoundError")


def includeme(config):
    config.register_service_factory(
        "lms.services.hapi.HypothesisAPIService", name="hapi"
    )
