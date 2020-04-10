import pytest

from lms.authentication._helpers import authenticated_userid, get_lti_user, groupfinder
from lms.models import LTIUser
from lms.validation import ValidationError


class TestAuthenticatedUserID:
    @pytest.mark.parametrize(
        "lti_user,expected_userid",
        [
            (
                LTIUser(
                    "sam", "Hypothesisf301584250a2dece14f021ab8424018a", "TEST_ROLES"
                ),
                "c2Ft:Hypothesisf301584250a2dece14f021ab8424018a",
            ),
            (
                LTIUser(
                    "Sam:Smith",
                    "Hypothesisf301584250a2dece14f021ab8424018a",
                    "TEST_ROLES",
                ),
                "U2FtOlNtaXRo:Hypothesisf301584250a2dece14f021ab8424018a",
            ),
        ],
    )
    def test_it(self, lti_user, expected_userid):
        assert authenticated_userid(lti_user) == expected_userid


class TestGetLTIUser:
    def test_it_returns_the_LTIUser_from_LaunchParamsAuthSchema(
        self,
        bearer_token_schema,
        LaunchParamsAuthSchema,
        launch_params_auth_schema,
        pyramid_request,
    ):
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        lti_user = get_lti_user(pyramid_request)

        LaunchParamsAuthSchema.assert_called_once_with(pyramid_request)
        launch_params_auth_schema.lti_user.assert_called_once_with()
        assert lti_user == launch_params_auth_schema.lti_user.return_value

    def test_if_LaunchParamsAuthSchema_fails_it_falls_back_on_BearerTokenSchema(
        self,
        launch_params_auth_schema,
        BearerTokenSchema,
        bearer_token_schema,
        pyramid_request,
    ):
        launch_params_auth_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        lti_user = get_lti_user(pyramid_request)

        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.lti_user.assert_called_once_with()
        assert lti_user == bearer_token_schema.lti_user.return_value

    def test_if_LaunchParamsAuthSchema_and_BearerTokenSchema_fails_it_falls_back_on_CanvasOAuthCallbackSchema(
        self,
        launch_params_auth_schema,
        bearer_token_schema,
        CanvasOAuthCallbackSchema,
        canvas_oauth_callback_schema,
        pyramid_request,
    ):
        launch_params_auth_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        lti_user = get_lti_user(pyramid_request)

        CanvasOAuthCallbackSchema.assert_called_once_with(pyramid_request)
        canvas_oauth_callback_schema.lti_user.assert_called_once_with()
        assert lti_user == canvas_oauth_callback_schema.lti_user.return_value

    def test_it_returns_None_if_all_schemas_fail(
        self,
        launch_params_auth_schema,
        bearer_token_schema,
        canvas_oauth_callback_schema,
        pyramid_request,
    ):
        launch_params_auth_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        bearer_token_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        canvas_oauth_callback_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )

        assert get_lti_user(pyramid_request) is None

    def test_LaunchParamsAuthSchema_overrides_BearerTokenSchema(
        self, launch_params_auth_schema, pyramid_request
    ):
        assert (
            get_lti_user(pyramid_request)
            == launch_params_auth_schema.lti_user.return_value
        )


class TestGroupFinder:
    def test_find_group(self, pyramid_request):
        userid = "report_viewer"
        groups = groupfinder(userid, pyramid_request)

        assert groups is not None
        assert "report_viewers" in groups

    def test_not_find_group(self, pyramid_request):
        userid = "wrongid"

        groups = groupfinder(userid, pyramid_request)

        assert not groups


@pytest.fixture(autouse=True)
def BearerTokenSchema(patch):
    return patch("lms.authentication._helpers.BearerTokenSchema")


@pytest.fixture
def bearer_token_schema(BearerTokenSchema):
    return BearerTokenSchema.return_value


@pytest.fixture(autouse=True)
def CanvasOAuthCallbackSchema(patch):
    return patch("lms.authentication._helpers.CanvasOAuthCallbackSchema")


@pytest.fixture
def canvas_oauth_callback_schema(CanvasOAuthCallbackSchema):
    return CanvasOAuthCallbackSchema.return_value


@pytest.fixture(autouse=True)
def LaunchParamsAuthSchema(patch):
    return patch("lms.authentication._helpers.LaunchParamsAuthSchema")


@pytest.fixture
def launch_params_auth_schema(LaunchParamsAuthSchema):
    return LaunchParamsAuthSchema.return_value
