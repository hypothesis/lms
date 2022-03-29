import pytest
from pyramid import testing

from lms.validation import ConfigureAssignmentSchema


class TestConfigureAssignmentSchema:
    def test_that_validation_succeeds_for_valid_requests(self, schema):
        schema.parse()

    @pytest.fixture
    def pyramid_request(self):
        pyramid_request = testing.DummyRequest()
        pyramid_request.params["lti_version"] = "LTI-1p0"
        pyramid_request.params["roles"] = "INSTRUCTOR"

        pyramid_request.params["document_url"] = "test_document_url"
        pyramid_request.params["resource_link_id"] = "test_resource_link_id"
        pyramid_request.params["oauth_consumer_key"] = "test_oauth_consumer_key"
        pyramid_request.params["user_id"] = "test_user_id"
        pyramid_request.params["context_id"] = "test_context_id"
        pyramid_request.params["context_title"] = "test_context_title"
        pyramid_request.params[
            "tool_consumer_instance_guid"
        ] = "test_tool_consumer_instance_guid"
        return pyramid_request

    @pytest.fixture
    def schema(self, pyramid_request):
        return ConfigureAssignmentSchema(pyramid_request)
