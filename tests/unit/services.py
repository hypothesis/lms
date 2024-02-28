from unittest import mock

import pytest

from lms.product.plugin.course_copy import (
    CourseCopyFilesHelper,
    CourseCopyGroupsHelper,
    CourseCopyPlugin,
)
from lms.product.plugin.grouping import GroupingPlugin
from lms.product.plugin.misc import MiscPlugin
from lms.services import CanvasService, LTIRoleService, OrganizationService
from lms.services.aes import AESService
from lms.services.application_instance import ApplicationInstanceService
from lms.services.assignment import AssignmentService
from lms.services.async_oauth_http import AsyncOAuthHTTPService
from lms.services.blackboard_api.client import BlackboardAPIClient
from lms.services.canvas_api import CanvasAPIClient
from lms.services.canvas_studio import CanvasStudioService
from lms.services.course import CourseService
from lms.services.d2l_api import D2LAPIClient
from lms.services.digest import DigestService
from lms.services.email_preferences import EmailPreferencesService
from lms.services.event import EventService
from lms.services.file import FileService
from lms.services.grading_info import GradingInfoService
from lms.services.grant_token import GrantTokenService
from lms.services.group_info import GroupInfoService
from lms.services.grouping import GroupingService
from lms.services.h_api import HAPI
from lms.services.http import HTTPService
from lms.services.jstor import JSTORService
from lms.services.jwt import JWTService
from lms.services.jwt_oauth2_token import JWTOAuth2TokenService
from lms.services.launch_verifier import LaunchVerifier
from lms.services.lti_grading import LTIGradingService
from lms.services.lti_h import LTIHService
from lms.services.lti_registration import LTIRegistrationService
from lms.services.lti_user import LTIUserService
from lms.services.ltia_http import LTIAHTTPService
from lms.services.mailchimp import MailchimpService
from lms.services.moodle import MoodleAPIClient
from lms.services.oauth1 import OAuth1Service
from lms.services.oauth2_token import OAuth2TokenService
from lms.services.oauth_http import OAuthHTTPService
from lms.services.rsa_key import RSAKeyService
from lms.services.user import UserService
from lms.services.user_preferences import UserPreferencesService
from lms.services.vitalsource import VitalSourceService
from lms.services.youtube import YouTubeService
from tests import factories

__all__ = (
    # Meta fixture for creating service fixtures
    "mock_service",
    # Individual services
    "aes_service",
    "application_instance_service",
    "assignment_service",
    "async_oauth_http_service",
    "blackboard_api_client",
    "canvas_api_client",
    "canvas_service",
    "canvas_studio_service",
    "course_service",
    "d2l_api_client",
    "digest_service",
    "event_service",
    "file_service",
    "grading_info_service",
    "grant_token_service",
    "group_info_service",
    "grouping_service",
    "h_api",
    "http_service",
    "jstor_service",
    "jwt_service",
    "jwt_oauth2_token_service",
    "launch_verifier",
    "lti_grading_service",
    "lti_h_service",
    "lti_registration_service",
    "lti_role_service",
    "lti_user_service",
    "ltia_http_service",
    "mailchimp_service",
    "moodle_api_client",
    "oauth1_service",
    "oauth2_token_service",
    "oauth_http_service",
    "organization_service",
    "rsa_key_service",
    "user_service",
    "user_preferences_service",
    "vitalsource_service",
    "email_preferences_service",
    "youtube_service",
    # Product plugins
    "grouping_plugin",
    "course_copy_plugin",
    "course_copy_files_helper",
    "course_copy_groups_helper",
    "misc_plugin",
)


@pytest.fixture
def mock_service(pyramid_config):
    def mock_service(service_class, service_name=None):
        mock_service = mock.create_autospec(service_class, spec_set=True, instance=True)

        if service_name:
            pyramid_config.register_service(mock_service, name=service_name)
        else:
            pyramid_config.register_service(mock_service, iface=service_class)

        return mock_service

    return mock_service


@pytest.fixture
def application_instance_service(mock_service, application_instance):
    application_instance_service = mock_service(
        ApplicationInstanceService, service_name="application_instance"
    )
    application_instance_service.get_by_consumer_key.return_value = application_instance

    return application_instance_service


@pytest.fixture
def aes_service(mock_service):
    aes_service = mock_service(AESService)
    # Don't return MagicMock objects from these functions so the output can
    # be tested against things which store them in the DB
    aes_service.encrypt.return_value = b"fake_ciphertext"
    aes_service.build_iv.return_value = b"fake_aes_iv"
    return aes_service


@pytest.fixture
def assignment_service(mock_service):
    return mock_service(AssignmentService, service_name="assignment")


@pytest.fixture
def blackboard_api_client(mock_service):
    return mock_service(BlackboardAPIClient, service_name="blackboard_api_client")


@pytest.fixture
def canvas_api_client(mock_service):
    canvas_api_client = mock_service(CanvasAPIClient, service_name="canvas_api_client")

    canvas_api_client.get_token.return_value = (
        "test_access_token",
        "test_refresh_token",
        3600,
    )
    return canvas_api_client


@pytest.fixture
def canvas_service(mock_service, canvas_api_client):
    canvas_service = mock_service(CanvasService)
    canvas_service.api = canvas_api_client

    return canvas_service


@pytest.fixture
def canvas_studio_service(mock_service):
    return mock_service(CanvasStudioService)


@pytest.fixture
def course_service(mock_service):
    return mock_service(CourseService, service_name="course")


@pytest.fixture
def d2l_api_client(mock_service):
    return mock_service(D2LAPIClient)


@pytest.fixture
def moodle_api_client(mock_service):
    return mock_service(MoodleAPIClient)


@pytest.fixture
def digest_service(mock_service):
    return mock_service(DigestService)


@pytest.fixture
def event_service(mock_service):
    return mock_service(EventService)


@pytest.fixture
def file_service(mock_service):
    return mock_service(FileService, service_name="file")


@pytest.fixture
def grading_info_service(mock_service):
    return mock_service(GradingInfoService, service_name="grading_info")


@pytest.fixture
def grant_token_service(mock_service):
    return mock_service(GrantTokenService, service_name="grant_token")


@pytest.fixture
def group_info_service(mock_service):
    return mock_service(GroupInfoService, service_name="group_info")


@pytest.fixture
def grouping_service(mock_service):
    return mock_service(GroupingService, service_name="grouping")


@pytest.fixture
def h_api(mock_service):
    h_api = mock_service(HAPI)
    h_api.get_user.return_value = factories.HUser()

    return h_api


@pytest.fixture
def http_service(mock_service):
    http_service = mock_service(HTTPService, service_name="http")
    http_service.request.return_value = factories.requests.Response()

    return http_service


@pytest.fixture
def jstor_service(mock_service):
    return mock_service(JSTORService)


@pytest.fixture
def youtube_service(mock_service):
    return mock_service(YouTubeService)


@pytest.fixture
def jwt_service(mock_service):
    return mock_service(JWTService)


@pytest.fixture
def jwt_oauth2_token_service(mock_service):
    return mock_service(JWTOAuth2TokenService)


@pytest.fixture
def oauth_http_service(mock_service):
    oauth_http_service = mock_service(OAuthHTTPService, service_name="oauth_http")
    oauth_http_service.request.return_value = factories.requests.Response()
    return oauth_http_service


@pytest.fixture
def async_oauth_http_service(mock_service):
    async_oauth_http_service = mock_service(
        AsyncOAuthHTTPService, service_name="async_oauth_http"
    )
    return async_oauth_http_service


@pytest.fixture
def organization_service(mock_service):
    return mock_service(OrganizationService)


@pytest.fixture
def launch_verifier(mock_service):
    return mock_service(LaunchVerifier, service_name="launch_verifier")


@pytest.fixture
def lti_grading_service(mock_service):
    return mock_service(LTIGradingService)


@pytest.fixture
def lti_h_service(mock_service):
    return mock_service(LTIHService, service_name="lti_h")


@pytest.fixture
def lti_registration_service(mock_service):
    return mock_service(LTIRegistrationService)


@pytest.fixture
def lti_role_service(mock_service):
    return mock_service(LTIRoleService)


@pytest.fixture
def ltia_http_service(mock_service):
    return mock_service(LTIAHTTPService)


@pytest.fixture
def mailchimp_service(mock_service):
    return mock_service(MailchimpService, service_name="mailchimp")


@pytest.fixture
def oauth1_service(mock_service):
    return mock_service(OAuth1Service, service_name="oauth1")


@pytest.fixture
def oauth2_token_service(mock_service, oauth_token):
    oauth2_token_service = mock_service(OAuth2TokenService, service_name="oauth2_token")
    oauth2_token_service.get.return_value = oauth_token

    return oauth2_token_service


@pytest.fixture
def rsa_key_service(mock_service):
    return mock_service(RSAKeyService)


@pytest.fixture
def user_service(mock_service):
    return mock_service(UserService)


@pytest.fixture
def user_preferences_service(mock_service):
    return mock_service(UserPreferencesService)


@pytest.fixture
def lti_user_service(mock_service):
    return mock_service(LTIUserService)


@pytest.fixture
def vitalsource_service(mock_service):
    return mock_service(VitalSourceService)


@pytest.fixture
def email_preferences_service(mock_service):
    return mock_service(EmailPreferencesService)


@pytest.fixture
def course_copy_files_helper(mock_service):
    return mock_service(CourseCopyFilesHelper)


@pytest.fixture
def course_copy_groups_helper(mock_service):
    return mock_service(CourseCopyGroupsHelper)


@pytest.fixture
def course_copy_plugin(mock_service):
    return mock_service(CourseCopyPlugin)


@pytest.fixture
def grouping_plugin(mock_service):
    return mock_service(GroupingPlugin)


@pytest.fixture
def misc_plugin(mock_service):
    return mock_service(MiscPlugin)
