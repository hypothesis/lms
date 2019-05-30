from pyramid import testing
import pytest

from lms.validation import ConfigureModuleItemSchema, parser
from lms.validation import ValidationError


class TestConfigureModuleItemSchema:
    def test_that_validation_succeeds_for_valid_requests(self, pyramid_request, schema):
        self.parse(schema, pyramid_request)

    @pytest.mark.parametrize(
        "param", ["document_url", "resource_link_id", "tool_consumer_instance_guid"]
    )
    def test_that_validation_fails_if_a_required_param_is_missing(
        self, param, pyramid_request, schema
    ):
        del pyramid_request.params[param]

        with pytest.raises(ValidationError) as exc_info:
            self.parse(schema, pyramid_request)

        assert exc_info.value.messages == dict(
            [(param, ["Missing data for required field."])]
        )

    def parse(self, schema, request):
        """Parse ``request`` with ``schema`` and return the parsed params."""
        return parser.parse(schema, request, locations=["form"])

    @pytest.fixture
    def pyramid_request(self):
        """Return a minimal valid OAuth 2 redirect request."""
        pyramid_request = testing.DummyRequest()
        pyramid_request.params["document_url"] = "test_document_url"
        pyramid_request.params["resource_link_id"] = "test_resource_link_id"
        pyramid_request.params[
            "tool_consumer_instance_guid"
        ] = "test_tool_consumer_instance_guid"
        return pyramid_request

    @pytest.fixture
    def schema(self, pyramid_request):
        return ConfigureModuleItemSchema(pyramid_request)
