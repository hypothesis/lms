from unittest import mock

import pytest
from pyramid.testing import DummyRequest

from lms.resources import LTILaunchResource
from lms.views.predicates import (
    AuthorizedToConfigureAssignments,
    BlackboardCopied,
    BrightspaceCopied,
    CanvasFile,
    Configured,
    DBConfigured,
    LegacySpeedGrader,
    URLConfigured,
)
from tests import factories

pytestmark = pytest.mark.usefixtures("assignment_service")


class TestLegacySpeedGrader:
    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_legacy_speed_grading(self, pyramid_request, value, expected, context):
        context.is_legacy_speedgrader = True

        predicate = LegacySpeedGrader(value, mock.sentinel.config)

        result = predicate(context, pyramid_request)

        assert result is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_no_legacy_speed_grading(
        self, pyramid_request, value, expected, context
    ):
        context.is_legacy_speedgrader = False

        predicate = LegacySpeedGrader(value, mock.sentinel.config)

        result = predicate(context, pyramid_request)

        assert result is expected


class TestDBConfigured:
    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_theres_a_matching_assignment_config_in_the_db(
        self, pyramid_request, assignment_service, value, expected, context
    ):
        assignment_service.exists.return_value = True

        predicate = DBConfigured(value, mock.sentinel.config)

        result = predicate(context, pyramid_request)

        assert result is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_theres_no_matching_assignment_config_in_the_db(
        self, assignment_service, pyramid_request, value, expected, context
    ):
        assignment_service.exists.return_value = False

        predicate = DBConfigured(value, mock.sentinel.config)

        result = predicate(context, pyramid_request)

        assert result is expected


@pytest.mark.parametrize("PredicateClass", [BlackboardCopied, BrightspaceCopied])
class TestFooCopied:
    @pytest.mark.parametrize("resource_link_id_exists", [True, False])
    @pytest.mark.parametrize("resource_link_id_history_exists", [True, False])
    def test_it(
        self,
        assignment_service,
        PredicateClass,
        pyramid_request,
        resource_link_id_exists,
        resource_link_id_history_exists,
        context,
    ):
        def exists(_, resource_link_id, _resource_link_id_exists=None):
            if resource_link_id == pyramid_request.params["resource_link_id"]:
                if resource_link_id_exists:
                    # The database already has a document_url for the resource_link_id.
                    return True

            if resource_link_id == pyramid_request.params[PredicateClass.param_name]:
                if resource_link_id_history_exists:
                    # The database has a document_url for the resource_link_id_history.
                    return True

            return False

        assignment_service.exists.side_effect = exists

        # If there's no Assignment for resource_link_id in the DB
        # but there *is* a Assignment for resource_link_id_history
        # then we have a Blackboard copied assignment.
        expected_result = (
            resource_link_id_history_exists and not resource_link_id_exists
        )

        predicate = PredicateClass(True, mock.sentinel.config)
        assert predicate(context, pyramid_request) == expected_result

        predicate = PredicateClass(False, mock.sentinel.config)
        assert predicate(context, pyramid_request) == (not expected_result)

    def test_with_request_params_missing(
        self, PredicateClass, pyramid_request, context
    ):
        pyramid_request.params = {}

        predicate = PredicateClass(True, mock.sentinel.config)
        assert not predicate(context, pyramid_request)

        predicate = PredicateClass(False, mock.sentinel.config)
        assert predicate(context, pyramid_request)

    @pytest.fixture
    def pyramid_request(self, PredicateClass, pyramid_request):
        pyramid_request.params[
            PredicateClass.param_name
        ] = "test_resource_link_id_history"
        return pyramid_request


class TestCanvasFile:
    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_assignment_is_canvas_file(
        self, value, expected, context, pyramid_request
    ):
        pyramid_request.params = {"canvas_file": 22}
        predicate = CanvasFile(value, mock.sentinel.config)

        assert predicate(context, pyramid_request) is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_assignment_is_not_canvas_file(
        self, value, expected, pyramid_request, assignment_service, context
    ):
        assignment_service.exists.return_value = expected

        predicate = CanvasFile(value, mock.sentinel.config)

        assert predicate(context, pyramid_request) is expected


class TestURLConfigured:
    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_assignment_is_url_configured(
        self, value, expected, context, pyramid_request
    ):
        pyramid_request.params = {"url": "https://example.com"}

        predicate = URLConfigured(value, mock.sentinel.config)

        assert predicate(context, pyramid_request) is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_assignment_is_not_url_configured(
        self, value, expected, context, pyramid_request, assignment_service
    ):
        assignment_service.exists.return_value = expected

        predicate = URLConfigured(value, mock.sentinel.config)

        assert predicate(context, pyramid_request) is expected


class TestConfigured:
    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_assignment_is_url_configured(
        self, pyramid_request, value, expected, context
    ):
        pyramid_request.params = {"url": "https://example.com"}
        predicate = Configured(value, mock.sentinel.config)

        assert predicate(context, pyramid_request) is expected

    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_assignment_is_canvas_file(
        self, pyramid_request, value, expected, context
    ):
        pyramid_request.params = {"canvas_file": 22}
        predicate = Configured(value, mock.sentinel.config)

        assert predicate(context, pyramid_request) is expected

    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_assignment_is_db_configured(
        self, pyramid_request, assignment_service, value, expected, context
    ):
        assignment_service.exists.return_value = True

        predicate = Configured(value, mock.sentinel.config)

        assert predicate(context, pyramid_request) is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_assignment_is_unconfigured(
        self, assignment_service, pyramid_request, value, expected, context
    ):
        assignment_service.exists.return_value = False

        predicate = Configured(value, mock.sentinel.config)

        assert predicate(context, pyramid_request) is expected

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            "resource_link_id": "test_resource_link_id",
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
        }
        return pyramid_request

    @pytest.fixture(autouse=True)
    def assignment_service(self, assignment_service):
        # Make sure that the assignment is *not* DB-configured by default in
        # these tests.
        assignment_service.exists.return_value = False
        return assignment_service


class TestAuthorizedToConfigureAssignments:
    @pytest.mark.parametrize(
        "roles",
        [
            "administrator",
            "Administrator",
            "instructor",
            "Instructor",
            "teachingassistant",
            "TeachingAssistant",
            "Instructor,urn:lti:instrole:ims/lis/Administrator",
        ],
    )
    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_user_is_authorized(self, roles, value, expected, context):
        request = DummyRequest()
        request.lti_user = factories.LTIUser(roles=roles)
        predicate = AuthorizedToConfigureAssignments(value, mock.sentinel.config)

        assert predicate(context, request) is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_user_isnt_authorized(self, value, expected, context):
        request = DummyRequest()
        request.lti_user = factories.LTIUser(roles="Learner")
        predicate = AuthorizedToConfigureAssignments(value, mock.sentinel.config)

        assert predicate(context, request) is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_theres_no_lti_user(self, value, expected, context):
        request = DummyRequest()
        request.lti_user = None
        predicate = AuthorizedToConfigureAssignments(value, mock.sentinel.config)

        assert predicate(context, request) is expected


@pytest.fixture
def context(pyramid_request):
    context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
    context.resource_link_id = pyramid_request.params["resource_link_id"]

    return context
