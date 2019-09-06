from lms.services.exceptions import ServiceError
from lms.services.exceptions import LTILaunchVerificationError
from lms.services.exceptions import NoConsumerKey
from lms.services.exceptions import ConsumerKeyError
from lms.services.exceptions import LTIOAuthError
from lms.services.exceptions import ExternalRequestError
from lms.services.exceptions import HAPIError
from lms.services.exceptions import HAPINotFoundError
from lms.services.exceptions import CanvasAPIError
from lms.services.exceptions import CanvasAPIAccessTokenError
from lms.services.exceptions import CanvasAPIServerError

__all__ = (
    "ServiceError",
    "LTILaunchVerificationError",
    "NoConsumerKey",
    "ConsumerKeyError",
    "LTIOAuthError",
    "ExternalRequestError",
    "HAPIError",
    "HAPINotFoundError",
    "CanvasAPIError",
    "CanvasAPIAccessTokenError",
    "CanvasAPIServerError",
)


def includeme(config):
    config.register_service_factory(
        "lms.services.application_instance_getter.ApplicationInstanceGetter",
        name="ai_getter",
    )
    config.register_service_factory(
        "lms.services.canvas_api.CanvasAPIClient", name="canvas_api_client"
    )
    config.register_service_factory(
        "lms.services.h_api_client.HAPIClient", name="h_api_client"
    )
    config.register_service_factory(
        "lms.services.h_api_requests.HAPIRequests", name="h_api_requests"
    )
    config.register_service_factory(
        "lms.services.launch_verifier.LaunchVerifier", name="launch_verifier"
    )
    config.register_service_factory(
        "lms.services.lis_result_sourcedid.LISResultSourcedIdService",
        name="lis_result_sourcedid",
    )
    config.register_service_factory(
        "lms.services.lti_outcomes.LTIOutcomesClient", name="lti_outcomes_client"
    )
