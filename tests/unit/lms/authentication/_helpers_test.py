from unittest.mock import call

import pytest

from lms.authentication._helpers import authenticated_userid, get_lti_user, groupfinder
from lms.validation import ValidationError
from tests import factories


class TestAuthenticatedUserID:
    @pytest.mark.parametrize(
        "lti_user,expected_userid",
        [
            (
                factories.LTIUser(
                    user_id="sam",
                    oauth_consumer_key="Hypothesisf301584250a2dece14f021ab8424018a",
                ),
                "c2Ft:Hypothesisf301584250a2dece14f021ab8424018a",
            ),
            (
                factories.LTIUser(
                    user_id="Sam:Smith",
                    oauth_consumer_key="Hypothesisf301584250a2dece14f021ab8424018a",
                ),
                "U2FtOlNtaXRo:Hypothesisf301584250a2dece14f021ab8424018a",
            ),
        ],
    )
    def test_it(self, lti_user, expected_userid):
        assert authenticated_userid(lti_user) == expected_userid


class TestGetLTIUser:
    def test_it_returns_the_LTIUsers_from_LTI_launch_params(
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

    def test_it_returns_LTIUsers_from_authorization_headers(
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
        bearer_token_schema.lti_user.assert_called_once_with(location="headers")
        assert lti_user == bearer_token_schema.lti_user.return_value

    def test_it_returns_LTIUsers_from_authorization_query_string_params(
        self, launch_params_auth_schema, bearer_token_schema, pyramid_request,
    ):
        launch_params_auth_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        lti_user = factories.LTIUser()
        bearer_token_schema.lti_user.side_effect = [
            ValidationError(["TEST_ERROR_MESSAGE"]),
            lti_user,
            ValidationError(["TEST_ERROR_MESSAGE"]),
        ]

        returned_lti_user = get_lti_user(pyramid_request)

        assert bearer_token_schema.lti_user.call_args_list == [
            call(location="headers"),
            call(location="querystring"),
        ]
        assert returned_lti_user == lti_user

    def test_it_returns_LTIUsers_from_authorization_form_fields(
        self, launch_params_auth_schema, bearer_token_schema, pyramid_request,
    ):
        launch_params_auth_schema.lti_user.side_effect = ValidationError(
            ["TEST_ERROR_MESSAGE"]
        )
        lti_user = factories.LTIUser()
        bearer_token_schema.lti_user.side_effect = [
            ValidationError(["TEST_ERROR_MESSAGE"]),
            ValidationError(["TEST_ERROR_MESSAGE"]),
            lti_user,
        ]

        returned_lti_user = get_lti_user(pyramid_request)

        assert bearer_token_schema.lti_user.call_args_list == [
            call(location="headers"),
            call(location="querystring"),
            call(location="form"),
        ]
        assert returned_lti_user == lti_user

    def test_it_returns_LTIUsers_from_OAuth2_state_params(
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
