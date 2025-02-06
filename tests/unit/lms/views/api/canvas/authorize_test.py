from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest
from pyramid.httpexceptions import HTTPInternalServerError

from lms.resources._js_config import JSConfig
from lms.services import CanvasAPIServerError
from lms.views.api.canvas import authorize
from lms.views.api.canvas.authorize import ALL_SCOPES, SCOPES

pytestmark = pytest.mark.usefixtures(
    "application_instance_service", "course_service", "canvas_api_client"
)


class TestAuthorize:
    def test_it_redirects_to_the_right_Canvas_endpoint(self, pyramid_request):
        response = authorize.authorize(pyramid_request)

        assert response.status_code == 302
        assert response.location.startswith(
            f"{pyramid_request.lti_user.application_instance.lms_url}login/oauth2/auth"
        )

    def test_it_includes_the_client_id_in_a_query_param(self, pyramid_request):
        response = authorize.authorize(pyramid_request)

        query_params = parse_qs(urlparse(response.location).query)

        assert query_params["client_id"] == [
            str(pyramid_request.lti_user.application_instance.developer_key)
        ]

    def test_it_includes_the_response_type_in_a_query_param(self, pyramid_request):
        response = authorize.authorize(pyramid_request)

        query_params = parse_qs(urlparse(response.location).query)

        assert query_params["response_type"] == ["code"]

    def test_it_includes_the_redirect_uri_in_a_query_param(self, pyramid_request):
        response = authorize.authorize(pyramid_request)

        query_params = parse_qs(urlparse(response.location).query)

        assert query_params["redirect_uri"] == [
            "http://example.com/canvas_oauth_callback"
        ]

    def test_it_includes_the_scopes_in_a_query_param(self, pyramid_request):
        self.assert_sections_scopes(authorize.authorize(pyramid_request))

    @pytest.mark.usefixtures("no_courses_with_sections_enabled")
    def test_sections_enabled_alone_triggers_sections_scopes(self, pyramid_request):
        self.assert_sections_scopes(authorize.authorize(pyramid_request))

    @pytest.mark.usefixtures("sections_disabled")
    def test_another_course_with_sections_alone_triggers_sections_scopes(
        self, pyramid_request
    ):
        self.assert_sections_scopes(authorize.authorize(pyramid_request))

    @pytest.mark.usefixtures("sections_not_supported")
    def test_no_sections_scopes_if_sections_is_disabled(self, pyramid_request):
        self.assert_file_scopes_only(authorize.authorize(pyramid_request))

    @pytest.mark.usefixtures("no_courses_with_sections_enabled")
    @pytest.mark.usefixtures("sections_disabled")
    def test_no_sections_scopes_if_no_courses_and_disabled(self, pyramid_request):
        self.assert_file_scopes_only(authorize.authorize(pyramid_request))

    def test_it_includes_the_state_in_a_query_param(
        self, pyramid_request, OAuthCallbackSchema, canvas_oauth_callback_schema
    ):
        response = authorize.authorize(pyramid_request)

        query_params = parse_qs(urlparse(response.location).query)

        OAuthCallbackSchema.assert_called_once_with(pyramid_request)
        canvas_oauth_callback_schema.state_param.assert_called_once_with()
        assert query_params["state"] == [
            canvas_oauth_callback_schema.state_param.return_value
        ]

    @pytest.mark.parametrize("folders_enabled", [True, False])
    @pytest.mark.parametrize("groups_enabled", [True, False])
    @pytest.mark.parametrize("pages_enabled", [True, False])
    def test_setting_scopes(
        self, folders_enabled, groups_enabled, pages_enabled, pyramid_request
    ):
        pyramid_request.lti_user.application_instance.settings.set(
            "canvas", "folders_enabled", folders_enabled
        )
        pyramid_request.lti_user.application_instance.settings.set(
            "canvas", "pages_enabled", pages_enabled
        )
        pyramid_request.lti_user.application_instance.settings.set(
            "canvas", "groups_enabled", groups_enabled
        )

        response = authorize.authorize(pyramid_request)
        query_params = parse_qs(urlparse(response.location).query)
        scopes = set(query_params["scope"][0].split())

        if groups_enabled:
            assert set(SCOPES["groups"]).issubset(scopes)
        if folders_enabled:
            assert set(SCOPES["folders"]).issubset(scopes)
        if pages_enabled:
            assert set(SCOPES["pages"]).issubset(scopes)

    def assert_sections_scopes(self, response):
        query_params = parse_qs(urlparse(response.location).query)
        assert set(query_params["scope"][0].split(" ")) == set(
            SCOPES["files"] + SCOPES["sections"]
        )

    def assert_file_scopes_only(self, response):
        query_params = parse_qs(urlparse(response.location).query)
        assert set(query_params["scope"][0].split(" ")) == set(SCOPES["files"])

    @pytest.fixture
    def sections_not_supported(self, application_instance):
        application_instance.developer_key = None

    @pytest.fixture
    def sections_disabled(self, pyramid_request):
        pyramid_request.lti_user.application_instance.settings.set(
            "canvas",
            "sections_enabled",
            False,  # noqa: FBT003
        )

    @pytest.fixture
    def no_courses_with_sections_enabled(self, course_service):
        course_service.any_with_setting.return_value = False


class TestOAuth2Redirect:
    def test_it_gets_an_access_token_from_canvas(
        self, canvas_api_client, pyramid_request
    ):
        authorize.oauth2_redirect(pyramid_request)

        canvas_api_client.get_token.assert_called_once_with("test_authorization_code")

    def test_it_500s_if_get_token_raises(self, canvas_api_client, pyramid_request):
        canvas_api_client.get_token.side_effect = CanvasAPIServerError()

        with pytest.raises(HTTPInternalServerError):
            authorize.oauth2_redirect(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {"code": "test_authorization_code"}
        return pyramid_request


class TestOAuth2RedirectError:
    def test_it(self, pyramid_request):
        template_data = authorize.oauth2_redirect_error(pyramid_request)

        pyramid_request.context.js_config.enable_oauth2_redirect_error_mode.assert_called_with(
            auth_route="canvas_api.oauth.authorize",
            canvas_scopes=list(ALL_SCOPES),
        )
        assert not template_data

    def test_it_sets_the_invalid_scope_error_code_for_invalid_scope_errors(
        self, pyramid_request, LTIEvent, EventService
    ):
        pyramid_request.params["error"] = "invalid_scope"

        authorize.oauth2_redirect_error(pyramid_request)

        js_config = pyramid_request.context.js_config
        enable_oauth2_redirect_error_mode = js_config.enable_oauth2_redirect_error_mode
        error_code = enable_oauth2_redirect_error_mode.call_args[1].get("error_code")
        assert error_code == JSConfig.ErrorCode.CANVAS_INVALID_SCOPE
        LTIEvent.from_request.assert_called_once_with(
            request=pyramid_request,
            type_=LTIEvent.Type.ERROR_CODE,
            data={"code": JSConfig.ErrorCode.CANVAS_INVALID_SCOPE},
        )
        EventService.queue_event.assert_called_once_with(
            LTIEvent.from_request.return_value
        )

    def test_it_sets_the_error_details_if_theres_an_error_description(
        self, pyramid_request
    ):
        pyramid_request.params["error_description"] = mock.sentinel.error_description

        authorize.oauth2_redirect_error(pyramid_request)

        js_config = pyramid_request.context.js_config
        enable_oauth2_redirect_error_mode = js_config.enable_oauth2_redirect_error_mode
        error_details = enable_oauth2_redirect_error_mode.call_args[1].get(
            "error_details"
        )
        assert error_details == {"error_description": mock.sentinel.error_description}

    @pytest.fixture
    def pyramid_request(self, pyramid_request, OAuth2RedirectResource):
        context = OAuth2RedirectResource(pyramid_request)
        context.js_config = mock.create_autospec(JSConfig, spec_set=True, instance=True)
        context.js_config.ErrorCode = JSConfig.ErrorCode
        pyramid_request.context = context
        pyramid_request.params.clear()
        return pyramid_request

    @pytest.fixture(autouse=True)
    def OAuth2RedirectResource(self, patch):
        return patch("lms.resources.OAuth2RedirectResource")

    @pytest.fixture(autouse=True)
    def EventService(self, patch):
        return patch("lms.views.api.canvas.authorize.EventService")

    @pytest.fixture(autouse=True)
    def LTIEvent(self, patch):
        return patch("lms.views.api.canvas.authorize.LTIEvent")


@pytest.fixture(autouse=True)
def OAuthCallbackSchema(patch):
    return patch("lms.views.api.canvas.authorize.OAuthCallbackSchema")


@pytest.fixture
def canvas_oauth_callback_schema(OAuthCallbackSchema):
    schema = OAuthCallbackSchema.return_value
    schema.state_param.return_value = "test_state"
    return schema
