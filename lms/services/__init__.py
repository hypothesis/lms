from lms.services.exceptions import (
    CanvasAPIError,
    CanvasAPIPermissionError,
    CanvasAPIServerError,
    CanvasFileNotFoundInCourse,
    ConsumerKeyError,
    ExternalRequestError,
    HAPIError,
    LTILaunchVerificationError,
    LTIOAuthError,
    LTIOutcomesAPIError,
    NoOAuth2Token,
    ProxyAPIAccessTokenError,
    ProxyAPIError,
    ServiceError,
)


def includeme(config):
    config.register_service_factory(
        "lms.services.application_instance_getter.application_instance_getter_service_factory",
        name="ai_getter",
    )
    config.register_service_factory(
        "lms.services.canvas_api.canvas_api_client_factory", name="canvas_api_client"
    )
    config.register_service_factory("lms.services.h_api.HAPI", name="h_api")
    config.register_service_factory(
        "lms.services.launch_verifier.LaunchVerifier", name="launch_verifier"
    )
    config.register_service_factory(
        "lms.services.grading_info.GradingInfoService", name="grading_info"
    )
    config.register_service_factory(
        "lms.services.lti_outcomes.LTIOutcomesClient", name="lti_outcomes_client"
    )
    config.register_service_factory(
        "lms.services.group_info.GroupInfoService", name="group_info"
    )
    config.register_service_factory("lms.services.lti_h.LTIHService", name="lti_h")
    config.register_service_factory("lms.services.oauth1.OAuth1Service", name="oauth1")
    config.register_service_factory(
        "lms.services.course.course_service_factory", name="course"
    )
    config.register_service_factory(
        "lms.services.oauth2_token.oauth2_token_service_factory", name="oauth2_token"
    )
    config.register_service_factory(
        "lms.services.assignment.factory", name="assignment"
    )
    config.register_service_factory(
        "lms.services.vitalsource.factory", name="vitalsource"
    )
    config.register_service_factory(
        "lms.services.grant_token.factory", name="grant_token"
    )
    config.register_service_factory(
        "lms.services.application_instance.factory", name="application_instance"
    )
