from unittest import mock

import pytest

from lms.models import ApplicationSettings
from lms.services import CanvasService
from lms.services.application_instance import ApplicationInstanceService
from lms.services.assignment import AssignmentService
from lms.services.blackboard_api.client import BlackboardAPIClient
from lms.services.canvas_api import CanvasAPIClient
from lms.services.course import CourseService
from lms.services.file import FileService
from lms.services.grading_info import GradingInfoService
from lms.services.grant_token import GrantTokenService
from lms.services.group_info import GroupInfoService
from lms.services.grouping import GroupingService
from lms.services.h_api import HAPI
from lms.services.http import HTTPService
from lms.services.launch_verifier import LaunchVerifier
from lms.services.lti_h import LTIHService
from lms.services.lti_outcomes import LTIOutcomesClient
from lms.services.oauth1 import OAuth1Service
from lms.services.oauth2_token import OAuth2TokenService
from lms.services.oauth_http import OAuthHTTPService
from lms.services.vitalsource import VitalSourceService
from tests import factories

__all__ = (
    # Meta fixture for creating service fixtures
    "mock_service",
    # Individual services
    "application_instance_service",
    "assignment_service",
    "blackboard_api_client",
    "canvas_api_client",
    "canvas_service",
    "course_service",
    "grading_info_service",
    "grant_token_service",
    "group_info_service",
    "grouping_service",
    "http_service",
    "oauth_http_service",
    "launch_verifier",
    "lti_h_service",
    "lti_outcomes_client",
    "oauth1_service",
    "oauth2_token_service",
    "h_api",
    "vitalsource_service",
    "file_service",
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
def application_instance_service(mock_service):
    application_instance = factories.ApplicationInstance(
        consumer_key="TEST_OAUTH_CONSUMER_KEY",
        developer_key="TEST_DEVELOPER_KEY",
        provisioning=True,
        settings=ApplicationSettings({}),
    )
    application_instance.settings.set("canvas", "sections_enabled", True)
    application_instance.settings.set("canvas", "groups_enabled", False)

    application_instance_service = mock_service(
        ApplicationInstanceService, service_name="application_instance"
    )
    application_instance_service.get.return_value = application_instance
    application_instance_service.get_by_consumer_key.return_value = application_instance

    return application_instance_service


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
def course_service(mock_service):
    return mock_service(CourseService, service_name="course")


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
    h_api = mock_service(HAPI, service_name="h_api")
    h_api.get_user.return_value = factories.HUser()

    return h_api


@pytest.fixture
def http_service(mock_service):
    http_service = mock_service(HTTPService, service_name="http")
    http_service.request.return_value = factories.requests.Response()

    return http_service


@pytest.fixture
def oauth_http_service(mock_service):
    oauth_http_service = mock_service(OAuthHTTPService, service_name="oauth_http")
    oauth_http_service.request.return_value = factories.requests.Response()
    return oauth_http_service


@pytest.fixture
def launch_verifier(mock_service):
    return mock_service(LaunchVerifier, service_name="launch_verifier")


@pytest.fixture
def lti_outcomes_client(mock_service):
    return mock_service(LTIOutcomesClient, service_name="lti_outcomes_client")


@pytest.fixture
def lti_h_service(mock_service):
    return mock_service(LTIHService, service_name="lti_h")


@pytest.fixture
def oauth1_service(mock_service):
    return mock_service(OAuth1Service, service_name="oauth1")


@pytest.fixture
def oauth2_token_service(mock_service, oauth_token):
    oauth2_token_service = mock_service(OAuth2TokenService, service_name="oauth2_token")
    oauth2_token_service.get.return_value = oauth_token

    return oauth2_token_service


@pytest.fixture
def vitalsource_service(mock_service):
    return mock_service(VitalSourceService, service_name="vitalsource")


@pytest.fixture
def file_service(mock_service):
    return mock_service(FileService, service_name="file")
