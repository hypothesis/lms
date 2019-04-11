import pytest

from lms.authentication._helpers import get_lti_user
from lms.validation import ValidationError


class TestGetLTIUser:
    def test_it_returns_the_LTIUser_from_LaunchParamsSchema(
        self,
        bearer_token_schema,
        LaunchParamsSchema,
        launch_params_schema,
        pyramid_request,
    ):
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        lti_user = get_lti_user(pyramid_request)

        LaunchParamsSchema.assert_called_once_with(pyramid_request)
        launch_params_schema.lti_user.assert_called_once_with()
        assert lti_user == launch_params_schema.lti_user.return_value

    def test_if_LaunchParamsSchema_fails_it_falls_back_on_BearerTokenSchema(
        self,
        launch_params_schema,
        BearerTokenSchema,
        bearer_token_schema,
        pyramid_request,
    ):
        launch_params_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        lti_user = get_lti_user(pyramid_request)

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.lti_user.assert_called_once_with()
        assert lti_user == bearer_token_schema.lti_user.return_value

    def test_it_returns_None_if_both_schemas_fail(
        self, launch_params_schema, bearer_token_schema, pyramid_request
    ):
        launch_params_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        assert get_lti_user(pyramid_request) is None

    def test_LaunchParamsSchema_overrides_BearerTokenSchema(
        self, launch_params_schema, pyramid_request
    ):
        assert (
            get_lti_user(pyramid_request) == launch_params_schema.lti_user.return_value
        )


@pytest.fixture(autouse=True)
def BearerTokenSchema(patch):
    return patch("lms.authentication._helpers.BearerTokenSchema")


@pytest.fixture
def bearer_token_schema(BearerTokenSchema):
    return BearerTokenSchema.return_value


@pytest.fixture(autouse=True)
def LaunchParamsSchema(patch):
    return patch("lms.authentication._helpers.LaunchParamsSchema")


@pytest.fixture
def launch_params_schema(LaunchParamsSchema):
    return LaunchParamsSchema.return_value
