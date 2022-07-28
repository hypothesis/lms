from lms.services.aes import AESService
from lms.services.application_instance import ApplicationInstanceNotFound
from lms.services.canvas import CanvasService
from lms.services.document_url import DocumentURLService
from lms.services.event import EventService
from lms.services.exceptions import (
    BlackboardFileNotFoundInCourse,
    CanvasAPIError,
    CanvasAPIPermissionError,
    CanvasAPIServerError,
    CanvasFileNotFoundInCourse,
    ExternalAsyncRequestError,
    ExternalRequestError,
    OAuth2TokenError,
    SerializableError,
)
from lms.services.h_api import HAPIError
from lms.services.jstor import JSTORService
from lms.services.jwt import JWTService
from lms.services.launch_verifier import (
    ConsumerKeyLaunchVerificationError,
    LTILaunchVerificationError,
    LTIOAuthError,
)
from lms.services.lti_grading import LTIGradingService
from lms.services.lti_names_roles import LTINamesRolesService
from lms.services.lti_registration import LTIRegistrationService
from lms.services.lti_role_service import LTIRoleService
from lms.services.ltia_http import LTIAHTTPService
from lms.services.rsa_key import RSAKeyService
from lms.services.user import UserService
from lms.services.vitalsource import VitalSourceService


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
        "lms.services.lti_grading.service_factory", iface=LTIGradingService
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
        "lms.services.vitalsource.service_factory", iface=VitalSourceService
    )
    config.register_service_factory(
        "lms.services.grant_token.factory", name="grant_token"
    )
    config.register_service_factory(
        "lms.services.application_instance.factory", name="application_instance"
    )
    config.register_service_factory(
        "lms.services.grouping.service_factory", name="grouping"
    )
    config.register_service_factory("lms.services.file.factory", name="file")
    config.register_service_factory(
        "lms.services.jstor.service_factory", iface=JSTORService
    )
    config.register_service_factory(
        "lms.services.lti_names_roles.factory", iface=LTINamesRolesService
    )
    config.register_service_factory(
        "lms.services.lti_registration.factory", iface=LTIRegistrationService
    )
    config.register_service_factory(
        "lms.services.lti_role_service.service_factory", iface=LTIRoleService
    )
    config.register_service_factory("lms.services.aes.factory", iface=AESService)
    config.register_service_factory("lms.services.jwt.factory", iface=JWTService)
    config.register_service_factory("lms.services.rsa_key.factory", iface=RSAKeyService)
    config.register_service_factory(
        "lms.services.ltia_http.factory", iface=LTIAHTTPService
    )
    config.register_service_factory(
        "lms.services.document_url.factory", iface=DocumentURLService
    )
    config.register_service_factory("lms.services.event.factory", iface=EventService)
