from lms.services.exceptions import HAPIError

__all__ = ("HAPIError",)


def includeme(config):
    config.register_service_factory(
        "lms.services.hapi.HypothesisAPIService", name="hapi"
    )
