from unittest import mock

import pytest
from pyramid.testing import DummyRequest

from lms.values import LTIUser
from lms.views.predicates import (
    AuthorizedToConfigureAssignments,
    CanvasFile,
    Configured,
    DBConfigured,
    URLConfigured,
)


class TestDBConfigured:
    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_theres_a_matching_assignment_config_in_the_db(
        self, pyramid_request, value, expected, ModuleItemConfiguration
    ):
        ModuleItemConfiguration.get_document_url.return_value = "test_document_url"
        pyramid_request.params = {
            "resource_link_id": "test_resource_link_id",
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
        }
        predicate = DBConfigured(value, mock.sentinel.config)

        result = predicate(mock.sentinel.context, pyramid_request)

        ModuleItemConfiguration.get_document_url.assert_called_once_with(
            pyramid_request.db,
            "test_tool_consumer_instance_guid",
            "test_resource_link_id",
        )
        assert result is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_theres_no_matching_assignment_config_in_the_db(
        self, pyramid_request, value, expected, ModuleItemConfiguration
    ):
        ModuleItemConfiguration.get_document_url.return_value = None
        pyramid_request.params = {
            "resource_link_id": "test_resource_link_id",
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
        }
        predicate = DBConfigured(value, mock.sentinel.config)

        result = predicate(mock.sentinel.context, pyramid_request)
        ModuleItemConfiguration.get_document_url.assert_called_once_with(
            pyramid_request.db,
            "test_tool_consumer_instance_guid",
            "test_resource_link_id",
        )
        assert result is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_request_params_are_missing(
        self, pyramid_request, value, expected, ModuleItemConfiguration
    ):
        pyramid_request.params = {}
        ModuleItemConfiguration.get_document_url.return_value = None
        predicate = DBConfigured(value, mock.sentinel.config)

        result = predicate(mock.sentinel.context, pyramid_request)
        ModuleItemConfiguration.get_document_url.assert_called_once_with(
            pyramid_request.db, None, None
        )
        assert result is expected


class TestCanvasFile:
    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_assignment_is_canvas_file(self, value, expected):
        request = DummyRequest(params={"canvas_file": 22})
        predicate = CanvasFile(value, mock.sentinel.config)

        assert predicate(mock.sentinel.context, request) is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_assignment_is_not_canvas_file(self, value, expected):
        predicate = CanvasFile(value, mock.sentinel.config)

        assert predicate(mock.sentinel.context, DummyRequest()) is expected


class TestURLConfigured:
    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_assignment_is_url_configured(self, value, expected):
        request = DummyRequest(params={"url": "https://example.com"})
        predicate = URLConfigured(value, mock.sentinel.config)

        assert predicate(mock.sentinel.context, request) is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_assignment_is_not_url_configured(self, value, expected):
        predicate = URLConfigured(value, mock.sentinel.config)

        assert predicate(mock.sentinel.context, DummyRequest()) is expected


class TestConfigured:
    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_assignment_is_url_configured(self, pyramid_request, value, expected):
        pyramid_request.params = {"url": "https://example.com"}
        predicate = Configured(value, mock.sentinel.config)

        assert predicate(mock.sentinel.context, pyramid_request) is expected

    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_assignment_is_canvas_file(self, pyramid_request, value, expected):
        pyramid_request.params = {"canvas_file": 22}
        predicate = Configured(value, mock.sentinel.config)

        assert predicate(mock.sentinel.context, pyramid_request) is expected

    @pytest.mark.parametrize("value,expected", [(True, True), (False, False)])
    def test_when_assignment_is_db_configured(
        self, pyramid_request, value, expected, ModuleItemConfiguration
    ):
        ModuleItemConfiguration.get_document_url.return_value = "test_document_url"
        predicate = Configured(value, mock.sentinel.config)

        assert predicate(mock.sentinel.context, pyramid_request) is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_assignment_is_unconfigured(
        self, pyramid_request, value, expected, ModuleItemConfiguration
    ):
        ModuleItemConfiguration.get_document_url.return_value = None
        pyramid_request.params = {}
        predicate = Configured(value, mock.sentinel.config)

        assert predicate(mock.sentinel.context, pyramid_request) is expected

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {
            "resource_link_id": "test_resource_link_id",
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
        }
        return pyramid_request


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
    def test_when_user_is_authorized(self, roles, value, expected):
        request = DummyRequest()
        request.lti_user = LTIUser(
            user_id="TEST_USER_ID",
            oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY",
            roles=roles,
        )
        predicate = AuthorizedToConfigureAssignments(value, mock.sentinel.config)

        assert predicate(mock.sentinel.context, request) is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_user_isnt_authorized(self, value, expected):
        request = DummyRequest()
        request.lti_user = LTIUser(
            user_id="TEST_USER_ID",
            oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY",
            roles="Learner",
        )
        predicate = AuthorizedToConfigureAssignments(value, mock.sentinel.config)

        assert predicate(mock.sentinel.context, request) is expected

    @pytest.mark.parametrize("value,expected", [(True, False), (False, True)])
    def test_when_theres_no_lti_user(self, value, expected):
        request = DummyRequest()
        request.lti_user = None
        predicate = AuthorizedToConfigureAssignments(value, mock.sentinel.config)

        assert predicate(mock.sentinel.context, request) is expected


@pytest.fixture(autouse=True)
def ModuleItemConfiguration(patch):
    return patch("lms.views.predicates._lti_launch.ModuleItemConfiguration")
