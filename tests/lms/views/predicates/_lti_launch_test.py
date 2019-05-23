from unittest import mock

from pyramid.testing import DummyRequest
import pytest

from lms.models import ModuleItemConfiguration
from lms.views.predicates import (
    IsDBConfigured,
    IsCanvasFile,
    IsURLConfigured,
    IsConfigured,
    UserIsAuthorizedToConfigureAssignments,
)


class TestIsDBConfigured:
    def test_when_theres_a_matching_assignment_config_in_the_db(self, pyramid_request):
        pyramid_request.params = {
            "resource_link_id": "test_resource_link_id",
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
        }

        assert (
            IsDBConfigured(True, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is True
        )
        assert (
            IsDBConfigured(False, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is False
        )

    def test_when_theres_no_matching_assignment_config_in_the_db(self, pyramid_request):
        pyramid_request.params = {
            "resource_link_id": "doesnt_match",
            "tool_consumer_instance_guid": "doesnt_match",
        }

        assert (
            IsDBConfigured(True, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is False
        )
        assert (
            IsDBConfigured(False, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is True
        )

    def test_when_request_params_are_missing(self, pyramid_request):
        pyramid_request.params = {}

        assert (
            IsDBConfigured(True, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is False
        )
        assert (
            IsDBConfigured(False, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is True
        )

    @pytest.fixture(autouse=True)
    def module_item_configuration(self, pyramid_request):
        pyramid_request.db.add(
            ModuleItemConfiguration(
                resource_link_id="test_resource_link_id",
                tool_consumer_instance_guid="test_tool_consumer_instance_guid",
                document_url="test_document_url",
            )
        )


class TestIsCanvasFile:
    def test_when_assignment_is_canvas_file(self):
        request = DummyRequest(params={"canvas_file": 22})

        assert (
            IsCanvasFile(True, mock.sentinel.config)(mock.sentinel.context, request)
            is True
        )
        assert (
            IsCanvasFile(False, mock.sentinel.config)(mock.sentinel.context, request)
            is False
        )

    def test_when_assignment_is_not_canvas_file(self):
        assert (
            IsCanvasFile(True, mock.sentinel.config)(
                mock.sentinel.context, DummyRequest()
            )
            is False
        )
        assert (
            IsCanvasFile(False, mock.sentinel.config)(
                mock.sentinel.context, DummyRequest()
            )
            is True
        )


class TestIsURLConfigured:
    def test_when_assignment_is_url_configured(self):
        request = DummyRequest(params={"url": "https://example.com"})

        assert (
            IsURLConfigured(True, mock.sentinel.config)(mock.sentinel.context, request)
            is True
        )
        assert (
            IsURLConfigured(False, mock.sentinel.config)(mock.sentinel.context, request)
            is False
        )

    def test_when_assignment_is_not_url_configured(self):
        assert (
            IsURLConfigured(True, mock.sentinel.config)(
                mock.sentinel.context, DummyRequest()
            )
            is False
        )
        assert (
            IsURLConfigured(False, mock.sentinel.config)(
                mock.sentinel.context, DummyRequest()
            )
            is True
        )


class TestIsConfigured:
    def test_when_assignment_is_url_configured(self, pyramid_request):
        pyramid_request.params = {"url": "https://example.com"}

        assert (
            IsConfigured(True, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is True
        )
        assert (
            IsConfigured(False, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is False
        )

    def test_when_assignment_is_canvas_file(self, pyramid_request):
        pyramid_request.params = {"canvas_file": 22}

        assert (
            IsConfigured(True, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is True
        )
        assert (
            IsConfigured(False, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is False
        )

    def test_when_assignment_is_db_configured(self, pyramid_request):
        pyramid_request.db.add(
            ModuleItemConfiguration(
                resource_link_id="test_resource_link_id",
                tool_consumer_instance_guid="test_tool_consumer_instance_guid",
                document_url="test_document_url",
            )
        )

        assert (
            IsConfigured(True, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is True
        )
        assert (
            IsConfigured(False, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is False
        )

    def test_when_assignment_is_unconfigured(self, pyramid_request):
        pyramid_request.params = {}

        assert (
            IsConfigured(True, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is False
        )
        assert (
            IsConfigured(False, mock.sentinel.config)(
                mock.sentinel.context, pyramid_request
            )
            is True
        )

    @pytest.fixture
    def pyramid_request(self):
        return DummyRequest(
            params={
                "resource_link_id": "test_resource_link_id",
                "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
            }
        )


class TestUserIsAuthorizedToConfigureAssignments:
    def test_when_user_is_authorized(self):
        request = DummyRequest(params={"roles": "Instructor"})

        assert (
            UserIsAuthorizedToConfigureAssignments(True, mock.sentinel.config)(
                mock.sentinel.context, request
            )
            is True
        )
        assert (
            UserIsAuthorizedToConfigureAssignments(False, mock.sentinel.config)(
                mock.sentinel.context, request
            )
            is False
        )

    def test_when_user_isnt_authorized(self):
        request = DummyRequest(params={"roles": "Learner"})

        assert (
            UserIsAuthorizedToConfigureAssignments(True, mock.sentinel.config)(
                mock.sentinel.context, request
            )
            is False
        )
        assert (
            UserIsAuthorizedToConfigureAssignments(False, mock.sentinel.config)(
                mock.sentinel.context, request
            )
            is True
        )

    def test_when_theres_no_roles_param(self):
        assert (
            UserIsAuthorizedToConfigureAssignments(True, mock.sentinel.config)(
                mock.sentinel.context, DummyRequest()
            )
            is False
        )
        assert (
            UserIsAuthorizedToConfigureAssignments(False, mock.sentinel.config)(
                mock.sentinel.context, DummyRequest()
            )
            is True
        )
