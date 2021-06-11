from unittest import mock

import pytest

from lms.models import ApplicationSettings
from lms.services.application_instance import ApplicationInstanceService
from lms.services.assignment import AssignmentService
from lms.services.blackboard_api.service import BlackboardAPIClient
from lms.services.canvas_api import CanvasAPIClient
from lms.services.course import CourseService
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
from lms.services.vitalsource import VitalSourceService
from tests import factories

__all__ = (
    "application_instance_service",
    "assignment_service",
    "blackboard_api_client",
    "canvas_api_client",
    "course_service",
    "http_service",
    "launch_verifier",
    "grading_info_service",
    "grant_token_service",
    "group_info_service",
    "lti_h_service",
    "oauth1_service",
    "oauth2_token_service",
    "vitalsource_service",
    "h_api",
    "lti_outcomes_client",
)


@pytest.fixture
def application_instance_service(pyramid_config):
    application_instance_service = mock.create_autospec(
        ApplicationInstanceService, instance=True, spec_set=True
    )

    application_instance_service.get.return_value = factories.ApplicationInstance(
        consumer_key="TEST_OAUTH_CONSUMER_KEY",
        developer_key="TEST_DEVELOPER_KEY",
        provisioning=True,
        settings=ApplicationSettings({}),
    )

    application_instance_service.get.return_value.settings.set(
        "canvas", "sections_enabled", True
    )

    application_instance_service.get.return_value.settings.set(
        "canvas", "groups_enabled", False
    )

    pyramid_config.register_service(
        application_instance_service, name="application_instance"
    )
    return application_instance_service


@pytest.fixture
def assignment_service(pyramid_config):
    assignment_service = mock.create_autospec(
        AssignmentService, spec_set=True, instance=True
    )
    pyramid_config.register_service(assignment_service, name="assignment")
    return assignment_service


@pytest.fixture
def blackboard_api_client(pyramid_config):
    blackboard_api_client = mock.create_autospec(
        BlackboardAPIClient, spec_set=True, instance=True
    )
    pyramid_config.register_service(blackboard_api_client, name="blackboard_api_client")
    return blackboard_api_client


@pytest.fixture
def canvas_api_client(pyramid_config):
    canvas_api_client = mock.create_autospec(
        CanvasAPIClient, spec_set=True, instance=True
    )
    canvas_api_client.get_token.return_value = (
        "test_access_token",
        "test_refresh_token",
        3600,
    )
    pyramid_config.register_service(canvas_api_client, name="canvas_api_client")
    return canvas_api_client


@pytest.fixture
def course_service(pyramid_config):
    course_service = mock.create_autospec(CourseService, spec_set=True, instance=True)
    pyramid_config.register_service(course_service, name="course")
    return course_service


@pytest.fixture
def grading_info_service(pyramid_config):
    grading_info_service = mock.create_autospec(
        GradingInfoService, instance=True, spec_set=True
    )
    grading_info_service.get_by_assignment.return_value = []
    pyramid_config.register_service(grading_info_service, name="grading_info")
    return grading_info_service


@pytest.fixture
def grant_token_service(pyramid_config):
    grant_token_service = mock.create_autospec(
        GrantTokenService, instance=True, spec_set=True
    )
    pyramid_config.register_service(grant_token_service, name="grant_token")
    return grant_token_service


@pytest.fixture
def group_info_service(pyramid_config):
    group_info_service = mock.create_autospec(
        GroupInfoService, instance=True, spec_set=True
    )
    pyramid_config.register_service(group_info_service, name="group_info")
    return group_info_service


@pytest.fixture
def grouping_service(pyramid_config):
    grouping_service = mock.create_autospec(
        GroupingService, spec_set=True, instance=True
    )
    pyramid_config.register_service(grouping_service, name="grouping")
    return grouping_service


@pytest.fixture
def h_api(pyramid_config):
    h_api = mock.create_autospec(HAPI, spec_set=True, instance=True)
    h_api.get_user.return_value = factories.HUser()
    pyramid_config.register_service(h_api, name="h_api")
    return h_api


@pytest.fixture
def http_service(pyramid_config):
    http_service = mock.create_autospec(HTTPService, instance=True, spec_set=True)
    http_service.request.return_value = factories.requests.Response()
    pyramid_config.register_service(http_service, name="http")
    return http_service


@pytest.fixture
def launch_verifier(pyramid_config):
    launch_verifier = mock.create_autospec(LaunchVerifier, spec_set=True, instance=True)
    pyramid_config.register_service(launch_verifier, name="launch_verifier")
    return launch_verifier


@pytest.fixture
def lti_outcomes_client(pyramid_config):
    lti_outcomes_client = mock.create_autospec(
        LTIOutcomesClient, instance=True, spec_set=True
    )
    pyramid_config.register_service(lti_outcomes_client, name="lti_outcomes_client")
    return lti_outcomes_client


@pytest.fixture
def lti_h_service(pyramid_config):
    lti_h_service = mock.create_autospec(LTIHService, instance=True, spec_set=True)
    pyramid_config.register_service(lti_h_service, name="lti_h")
    return lti_h_service


@pytest.fixture
def oauth1_service(pyramid_config):
    oauth1_service = mock.create_autospec(OAuth1Service, instance=True, spec_set=True)
    pyramid_config.register_service(oauth1_service, name="oauth1")
    return oauth1_service


@pytest.fixture
def oauth2_token_service(oauth_token, pyramid_config):
    oauth2_token_service = mock.create_autospec(
        OAuth2TokenService, instance=True, spec_set=True
    )
    oauth2_token_service.get.return_value = oauth_token
    pyramid_config.register_service(oauth2_token_service, name="oauth2_token")
    return oauth2_token_service


@pytest.fixture
def vitalsource_service(pyramid_config):
    vitalsource_service = mock.create_autospec(
        VitalSourceService, instance=True, spec_set=True
    )
    pyramid_config.register_service(vitalsource_service, name="vitalsource")
    return vitalsource_service
