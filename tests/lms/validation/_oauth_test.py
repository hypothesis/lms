import pytest
from pyramid import testing

from lms.validation import CanvasOAuthCallbackSchema
from lms.validation import parser
from lms.validation import ValidationError
from lms.validation._helpers import instantiate_schema


class TestCanvasOauthCallbackSchema:
    def test_it_returns_the_parsed_args_for_a_valid_request(
        self, schema, valid_request
    ):
        parsed_args = parser.parse(schema, valid_request)

        assert parsed_args == {"code": "test_code", "state": "test_state"}

    def test_its_invalid_if_state_is_missing(self, schema, valid_request):
        del valid_request.params["state"]

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(schema, valid_request)

        assert exc_info.value.messages == {
            "state": ["Missing data for required field."]
        }

    def test_its_invalid_if_state_is_missing_from_the_session(
        self, schema, valid_request
    ):
        del valid_request.session["canvas_api_authorize_state"]

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(schema, valid_request)

        assert exc_info.value.messages == {
            "state": ["Invalid or missing state parameter."]
        }

    def test_its_invalid_if_state_isnt_a_string(self, schema, valid_request):
        valid_request.params["state"] = 23

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(schema, valid_request)

        assert exc_info.value.messages == {"state": ["Not a valid string."]}

    def test_its_invalid_if_state_is_the_wrong_string(self, schema, valid_request):
        valid_request.params["state"] = "the_wrong_string"

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(schema, valid_request)

        assert exc_info.value.messages == {
            "state": ["Invalid or missing state parameter."]
        }

    def test_it_removes_the_state_param_after_validating_it(
        self, schema, valid_request
    ):
        parsed_args = parser.parse(schema, valid_request)

        assert "canvas_api_authorize_state" not in valid_request.session

    def test_its_invalid_if_state_is_null(self, schema, valid_request):
        valid_request.params["state"] = None

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(schema, valid_request)

        assert exc_info.value.messages == {"state": ["Field may not be null."]}

    def test_its_invalid_if_code_is_missing(self, schema, valid_request):
        del valid_request.params["code"]

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(schema, valid_request)

        assert exc_info.value.messages == {"code": ["Missing data for required field."]}

    def test_its_invalid_if_code_isnt_a_string(self, schema, valid_request):
        valid_request.params["code"] = 23

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(schema, valid_request)

        assert exc_info.value.messages == {"code": ["Not a valid string."]}

    def test_its_invalid_if_code_is_null(self, schema, valid_request):
        valid_request.params["code"] = None

        with pytest.raises(ValidationError) as exc_info:
            parsed_args = parser.parse(schema, valid_request)

        assert exc_info.value.messages == {"code": ["Field may not be null."]}

    @pytest.fixture
    def schema(self, valid_request):
        return instantiate_schema(CanvasOAuthCallbackSchema, valid_request)

    @pytest.fixture
    def valid_request(self):
        """Return a minimal valid request.

        All required fields are present and valid.
        """
        valid_request = testing.DummyRequest()
        valid_request.params["code"] = "test_code"
        valid_request.params["state"] = "test_state"
        valid_request.session["canvas_api_authorize_state"] = "test_state"
        return valid_request
