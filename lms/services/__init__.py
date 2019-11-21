from lms.services.exceptions import (
    CanvasAPIAccessTokenError,
    CanvasAPIError,
    CanvasAPIServerError,
    ConsumerKeyError,
    ExternalRequestError,
    HAPIError,
    HAPINotFoundError,
    LTILaunchVerificationError,
    LTIOAuthError,
    LTIOutcomesAPIError,
    NoConsumerKey,
    ServiceError,
)

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
    "LTIOutcomesAPIError",
)


def includeme(config):
    config.register_service_factory(
        "lms.services.application_instance_getter.ApplicationInstanceGetter",
        name="ai_getter",
    )
    config.register_service_factory(
        "lms.services.canvas_api.CanvasAPIClient", name="canvas_api_client"
    )
    config.register_service_factory("lms.services.h_api.HAPI", name="h_api")
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
    config.register_service_factory(
        "lms.services.group_info_upsert.GroupInfoUpsert", name="group_info_upsert"
    )
    config.register_service_factory("lms.services.lti_h.LTIHService", name="lti_h")
