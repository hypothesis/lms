from lms.services.exceptions import ServiceError
from lms.services.exceptions import LTILaunchVerificationError
from lms.services.exceptions import NoConsumerKey
from lms.services.exceptions import ConsumerKeyError
from lms.services.exceptions import LTIOAuthError
from lms.services.exceptions import HAPIError
from lms.services.exceptions import HAPINotFoundError
from lms.services.exceptions import CanvasAPIError

__all__ = (
    "ServiceError",
    "LTILaunchVerificationError",
    "NoConsumerKey",
    "ConsumerKeyError",
    "LTIOAuthError",
    "HAPIError",
    "HAPINotFoundError",
    "CanvasAPIError",
)


def includeme(config):
    config.register_service_factory(
        "lms.services.hapi.HypothesisAPIService", name="hapi"
    )
    config.register_service_factory(
        "lms.services.application_instance_getter.ApplicationInstanceGetter",
        name="ai_getter",
    )
    config.register_service_factory(
        "lms.services.launch_verifier.LaunchVerifier", name="launch_verifier"
    )
    config.register_service_factory(
        "lms.services.canvas_api.CanvasAPIClient", name="canvas_api_client"
    )
