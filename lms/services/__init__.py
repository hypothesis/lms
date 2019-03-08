from lms.services.exceptions import ServiceError
from lms.services.exceptions import ConsumerKeyError
from lms.services.exceptions import HAPIError
from lms.services.exceptions import HAPINotFoundError

__all__ = ("ServiceError", "ConsumerKeyError", "HAPIError", "HAPINotFoundError")


def includeme(config):
    config.register_service_factory(
        "lms.services.hapi.HypothesisAPIService", name="hapi"
    )
    config.register_service_factory(
        "lms.services.application_instance_getter.ApplicationInstanceGetter",
        name="ai_getter",
    )
