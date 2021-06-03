from lms.services.application_instance import ApplicationInstanceService
from lms.services.assignment import AssignmentService
from lms.services.blackboard_api import BlackboardAPIClient
from lms.services.canvas_api import CanvasAPIClient
from lms.services.course import CourseService
from lms.services.exceptions import (
    CanvasAPIError,
    CanvasAPIPermissionError,
    CanvasAPIServerError,
    CanvasFileNotFoundInCourse,
    ConsumerKeyError,
    ExternalRequestError,
    HAPIError,
    HTTPError,
    HTTPValidationError,
    LTILaunchVerificationError,
    LTIOAuthError,
    LTIOutcomesAPIError,
    NoOAuth2Token,
    ProxyAPIAccessTokenError,
    ProxyAPIError,
    ServiceError,
)
from lms.services.grading_info import GradingInfoService
from lms.services.grant_token import GrantTokenService
from lms.services.group_info import GroupInfoService
from lms.services.h_api import HAPI
from lms.services.http import HTTPService
from lms.services.launch_verifier import LaunchVerifier
from lms.services.lti_h import LTIHService
from lms.services.lti_outcomes import LTIOutcomesClient
from lms.services.oauth1 import OAuth1Service
from lms.services.oauth2_token import OAuth2TokenService
from lms.services.vitalsource import VitalSourceService


def includeme(config):
    config.register_service_factory(
        "lms.services.application_instance.factory", iface=ApplicationInstanceService
    )
    config.register_service_factory(
        "lms.services.assignment.factory", iface=AssignmentService
    )
    config.register_service_factory(
        "lms.services.blackboard_api.factory", iface=BlackboardAPIClient
    )
    config.register_service_factory(
        "lms.services.canvas_api.canvas_api_client_factory", iface=CanvasAPIClient
    )
    config.register_service_factory(
        "lms.services.course.course_service_factory", iface=CourseService
    )
    config.register_service_factory(
        "lms.services.grading_info.GradingInfoService", iface=GradingInfoService
    )
    config.register_service_factory(
        "lms.services.grant_token.factory", iface=GrantTokenService
    )
    config.register_service_factory(
        "lms.services.group_info.GroupInfoService", iface=GroupInfoService
    )
    config.register_service_factory("lms.services.h_api.HAPI", iface=HAPI)
    config.register_service_factory("lms.services.http.factory", iface=HTTPService)
    config.register_service_factory(
        "lms.services.launch_verifier.LaunchVerifier", iface=LaunchVerifier
    )
    config.register_service_factory("lms.services.lti_h.LTIHService", iface=LTIHService)
    config.register_service_factory(
        "lms.services.lti_outcomes.LTIOutcomesClient", iface=LTIOutcomesClient
    )
    config.register_service_factory(
        "lms.services.oauth1.OAuth1Service", iface=OAuth1Service
    )
    config.register_service_factory(
        "lms.services.oauth2_token.oauth2_token_service_factory",
        iface=OAuth2TokenService,
    )
    config.register_service_factory(
        "lms.services.vitalsource.factory", iface=VitalSourceService
    )
