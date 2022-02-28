from lms.services.application_instance import ApplicationInstanceNotFound
from lms.services.canvas import CanvasService
from lms.services.exceptions import (
    BlackboardFileNotFoundInCourse,
    CanvasAPIError,
    CanvasAPIPermissionError,
    CanvasAPIServerError,
    CanvasFileNotFoundInCourse,
    ExternalAsyncRequestError,
    ExternalRequestError,
    OAuth2TokenError,
)
from lms.services.h_api import HAPIError
from lms.services.key import KeyService
from lms.services.launch_verifier import (
    ConsumerKeyLaunchVerificationError,
    LTILaunchVerificationError,
    LTIOAuthError,
)
from lms.services.user import UserService
from lms.services.jwt import JWTService


def includeme(config):
    config.register_service_factory("lms.services.http.factory", name="http")
    config.register_service_factory(
        "lms.services.oauth_http.factory", name="oauth_http"
    )
    config.register_service_factory(
        "lms.services.async_oauth_http.factory", name="async_oauth_http"
    )
    config.register_service_factory(
        "lms.services.blackboard_api.blackboard_api_client_factory",
        name="blackboard_api_client",
    )
    config.register_service_factory(
        "lms.services.canvas_api.canvas_api_client_factory", name="canvas_api_client"
    )
    config.register_service_factory("lms.services.canvas.factory", iface=CanvasService)
    config.register_service_factory("lms.services.user.factory", iface=UserService)

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
    config.register_service_factory("lms.services.grouping.factory", name="grouping")
    config.register_service_factory("lms.services.file.factory", name="file")

    config.register_service_factory("lms.services.key.factory", iface=KeyService)
    config.register_service_factory("lms.services.jwt.factory", iface=JWTService)
