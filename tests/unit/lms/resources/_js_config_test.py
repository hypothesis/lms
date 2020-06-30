import datetime
from unittest import mock

import jwt
import pytest

from lms.models import GradingInfo, HGroup
from lms.resources import CanvasOAuth2RedirectResource, LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.services import ConsumerKeyError, HAPIError


class TestJSConfig:
    """General unit tests for JSConfig."""

    def test_auth_url(self, config):
        assert config["canvas"]["authUrl"] == "http://example.com/api/canvas/authorize"


class TestEnableContentItemSelectionMode:
    def test_it(self, context, js_config):
        js_config.enable_content_item_selection_mode(
            mock.sentinel.form_action, mock.sentinel.form_fields
        )

        assert js_config.asdict()["mode"] == "content-item-selection"
        assert js_config.asdict()["filePicker"] == {
            "formAction": mock.sentinel.form_action,
            "formFields": mock.sentinel.form_fields,
            "google": {
                "clientId": "fake_client_id",
                "developerKey": "fake_developer_key",
                "origin": context.custom_canvas_api_domain,
            },
            "canvas": {
                "enabled": True,
                "ltiLaunchUrl": "http://example.com/lti_launches",
                "courseId": "test_course_id",
            },
        }

    def test_google_picker_origin_falls_back_to_lms_url_if_theres_no_custom_canvas_api_domain(
        self, ai_getter, context, js_config
    ):
        context.custom_canvas_api_domain = None

        js_config.enable_content_item_selection_mode(
            mock.sentinel.form_action, mock.sentinel.form_fields
        )

        ai_getter.lms_url.assert_called_once_with()
        assert (
            js_config.asdict()["filePicker"]["google"]["origin"]
            == ai_getter.lms_url.return_value
        )

    def test_it_doesnt_enable_the_canvas_file_picker_if_the_lms_isnt_Canvas(
        self, context, js_config
    ):
        context.is_canvas = False

        js_config.enable_content_item_selection_mode(
            mock.sentinel.form_action, mock.sentinel.form_fields
        )

        self.assert_canvas_file_picker_not_enabled(js_config)

    def test_it_doesnt_enable_the_canvas_file_picker_if_the_consumer_key_isnt_found_in_the_db(
        self, ai_getter, js_config
    ):
        ai_getter.developer_key.side_effect = ConsumerKeyError()

        js_config.enable_content_item_selection_mode(
            mock.sentinel.form_action, mock.sentinel.form_fields
        )

        self.assert_canvas_file_picker_not_enabled(js_config)

    def test_it_doesnt_enable_the_canvas_file_picker_if_we_dont_have_a_developer_key(
        self, ai_getter, js_config
    ):
        ai_getter.developer_key.return_value = None

        js_config.enable_content_item_selection_mode(
            mock.sentinel.form_action, mock.sentinel.form_fields
        )

        self.assert_canvas_file_picker_not_enabled(js_config)

    def test_it_doesnt_enable_the_canvas_file_picker_if_theres_no_custom_canvas_course_id(
        self, pyramid_request, js_config
    ):
        del pyramid_request.params["custom_canvas_course_id"]

        js_config.enable_content_item_selection_mode(
            mock.sentinel.form_action, mock.sentinel.form_fields
        )

        self.assert_canvas_file_picker_not_enabled(js_config)

    def assert_canvas_file_picker_not_enabled(self, js_config):
        assert not js_config.asdict()["filePicker"]["canvas"]["enabled"]
        assert "courseId" not in js_config.asdict()


class TestAddCanvasFileID:
    """Unit tests for JSConfig.add_canvas_file_id()."""

    def test_it_adds_the_viaCallbackUrl(self, js_config):
        js_config.add_canvas_file_id("example_canvas_file_id")

        assert (
            js_config.asdict()["api"]["viaCallbackUrl"]
            == "http://example.com/api/canvas/files/example_canvas_file_id/via_url"
        )

    def test_it_sets_the_canvas_file_id(self, js_config, submission_params):
        js_config.add_canvas_file_id("example_canvas_file_id")

        assert submission_params()["canvas_file_id"] == "example_canvas_file_id"


class TestAddDocumentURL:
    """Unit tests for JSConfig.add_document_url()."""

    def test_it_adds_the_via_url(self, js_config, pyramid_request, via_url):
        js_config.add_document_url("example_document_url")

        via_url.assert_called_once_with(pyramid_request, "example_document_url")
        assert js_config.asdict()["viaUrl"] == via_url.return_value

    def test_it_sets_the_document_url(self, js_config, submission_params):
        js_config.add_document_url("example_document_url")

        assert submission_params()["document_url"] == "example_document_url"


class TestAddCanvasFileIDAddDocumentURLCommon:
    """Tests common to both add_canvas_file_id() and add_document_url()."""

    def test_it_sets_the_canvas_submission_params(
        self, pyramid_request, method, submission_params
    ):
        method("canvas_file_id_or_document_url")

        assert (
            submission_params()["h_username"]
            == pyramid_request.lti_user.h_user.username
        )
        assert (
            submission_params()["lis_outcome_service_url"]
            == "example_lis_outcome_service_url"
        )
        assert (
            submission_params()["lis_result_sourcedid"]
            == "example_lis_result_sourcedid"
        )
        assert submission_params()["learner_canvas_user_id"] == "test_user_id"

    def test_it_doesnt_set_the_speedGrader_settings_if_the_LMS_isnt_Canvas(
        self, context, method, js_config
    ):
        context.is_canvas = False

        method("canvas_file_id_or_document_url")

        assert "speedGrader" not in js_config.asdict()["canvas"]

    def test_it_doesnt_set_the_speedGrader_settings_if_theres_no_lis_result_sourcedid(
        self, method, js_config, pyramid_request
    ):
        del pyramid_request.params["lis_result_sourcedid"]

        method("canvas_file_id_or_document_url")

        assert "speedGrader" not in js_config.asdict()["canvas"]

    def test_it_doesnt_set_the_speedGrader_settings_if_theres_no_lis_outcome_service_url(
        self, method, js_config, pyramid_request
    ):
        del pyramid_request.params["lis_outcome_service_url"]

        method("canvas_file_id_or_document_url")

        assert "speedGrader" not in js_config.asdict()["canvas"]

    @pytest.fixture(params=["add_canvas_file_id", "add_document_url"])
    def method(self, js_config, request):
        """Return the method to be tested."""
        return getattr(js_config, request.param)


class TestMaybeEnableGrading:
    def test_it_adds_the_grading_settings(
        self, js_config, grading_info_service, pyramid_request
    ):
        js_config.maybe_enable_grading()

        grading_info_service.get_by_assignment.assert_called_once_with(
            context_id="test_course_id",
            oauth_consumer_key=pyramid_request.lti_user.oauth_consumer_key,
            resource_link_id="TEST_RESOURCE_LINK_ID",
        )
        assert js_config.asdict()["grading"] == {
            "enabled": True,
            "assignmentName": "test_assignment_name",
            "courseName": "test_course_name",
            "students": [
                {
                    "LISOutcomeServiceUrl": f"test_lis_outcomes_service_url_{i}",
                    "LISResultSourcedId": f"test_lis_result_sourcedid_{i}",
                    "displayName": f"test_h_display_name_{i}",
                    "userid": f"acct:test_h_username_{i}@TEST_AUTHORITY",
                }
                for i in range(3)
            ],
        }

    @pytest.mark.usefixtures("user_is_learner")
    def test_it_does_nothing_if_the_user_isnt_an_instructor(self, js_config):
        js_config.maybe_enable_grading()

        assert not js_config.asdict().get("grading")

    def test_it_does_nothing_if_theres_no_lis_outcome_service_url(
        self, js_config, pyramid_request
    ):
        del pyramid_request.params["lis_outcome_service_url"]

        js_config.maybe_enable_grading()

        assert not js_config.asdict().get("grading")

    def test_it_does_nothing_in_Canvas(self, context, js_config):
        context.is_canvas = True

        js_config.maybe_enable_grading()

        assert not js_config.asdict().get("grading")

    @pytest.fixture
    def grading_info_service(self, grading_info_service):
        grading_info_service.get_by_assignment.return_value = [
            mock.create_autospec(
                GradingInfo,
                instance=True,
                spec_set=True,
                lis_result_sourcedid=f"test_lis_result_sourcedid_{i}",
                lis_outcome_service_url=f"test_lis_outcomes_service_url_{i}",
                h_username=f"test_h_username_{i}",
                h_display_name=f"test_h_display_name_{i}",
            )
            for i in range(3)
        ]
        return grading_info_service

    @pytest.fixture
    def context(self, context):
        context.is_canvas = False
        return context

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.lti_user = pyramid_request.lti_user._replace(roles="Instructor")
        pyramid_request.params["context_title"] = "test_course_name"
        pyramid_request.params["resource_link_title"] = "test_assignment_name"
        return pyramid_request


class TestMaybeSetFocusedUser:
    def test_it_does_nothing_if_theres_no_focused_user_param(
        self, js_config, pyramid_request
    ):
        del pyramid_request.params["focused_user"]

        js_config.maybe_set_focused_user()

        assert "focus" not in js_config.asdict()["hypothesisClient"]

    def test_it_sets_the_focused_user_if_theres_a_focused_user_param(
        self, h_api, js_config
    ):
        js_config.maybe_set_focused_user()

        # It gets the display name from the h API.
        h_api.get_user.assert_called_once_with("example_h_username")
        # It sets the focused user.
        assert js_config.asdict()["hypothesisClient"]["focus"] == {
            "user": {
                "username": "example_h_username",
                "displayName": h_api.get_user.return_value.display_name,
            }
        }

    def test_display_name_falls_back_to_a_default_value(self, h_api, js_config):
        h_api.get_user.side_effect = HAPIError()

        js_config.maybe_set_focused_user()

        assert (
            js_config.asdict()["hypothesisClient"]["focus"]["user"]["displayName"]
            == "(Couldn't fetch student name)"
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params["focused_user"] = "example_h_username"
        return pyramid_request


class TestJSConfigAuthToken:
    """Unit tests for the "authToken" sub-dict of JSConfig."""

    def test_it(
        self, authToken, bearer_token_schema, BearerTokenSchema, pyramid_request
    ):
        BearerTokenSchema.assert_called_once_with(pyramid_request)
        bearer_token_schema.authorization_param.assert_called_once_with(
            pyramid_request.lti_user
        )
        assert authToken == bearer_token_schema.authorization_param.return_value

    @pytest.fixture
    def authToken(self, config):
        return config["api"]["authToken"]


class TestJSConfigAPISync:
    """Unit tests for the api.sync sub-dict of JSConfig."""

    @pytest.mark.usefixtures("section_groups_on")
    def test_it(self, sync, pyramid_request, GroupInfo):
        assert sync == {
            "path": "/api/canvas/sync",
            "data": {
                "course": {
                    "context_id": "test_context_id",
                    "custom_canvas_course_id": "test_custom_canvas_course_id",
                },
                "lms": {
                    "tool_consumer_instance_guid": "test_tool_consumer_instance_guid"
                },
                "group_info": {
                    key: value
                    for key, value in pyramid_request.params.items()
                    if key in GroupInfo.columns.return_value
                },
            },
        }

    @pytest.mark.usefixtures("section_groups_on", "learner_canvas_user_id")
    def test_it_adds_learner_canvas_user_id_for_SpeedGrader_launches(self, sync):
        assert sync["data"]["learner"] == {
            "canvas_user_id": "test_learner_canvas_user_id"
        }

    def test_its_None_if_section_groups_isnt_enabled(self, sync):
        assert sync is None

    @pytest.fixture
    def sync(self, config):
        return config["api"]["sync"]

    @pytest.fixture
    def learner_canvas_user_id(self, pyramid_request):
        pyramid_request.params["learner_canvas_user_id"] = "test_learner_canvas_user_id"

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params.clear()
        pyramid_request.params.update(
            {
                "context_id": "test_context_id",
                "custom_canvas_course_id": "test_custom_canvas_course_id",
                "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
                "foo": "bar",  # This item should be missing from group_info.
            }
        )
        return pyramid_request


class TestJSConfigDebug:
    """Unit tests for the "debug" sub-dict of JSConfig."""

    @pytest.mark.usefixtures("user_is_learner")
    def test_it_contains_debugging_info_about_the_users_role(self, config):
        assert "role:learner" in config["tags"]

    @pytest.fixture
    def config(self, config):
        return config["debug"]


class TestJSConfigHypothesisClient:
    """Unit tests for the "hypothesisClient" sub-dict of JSConfig."""

    def test_it_contains_one_service_config(self, config):
        assert len(config["services"]) == 1

    def test_it_includes_the_api_url(self, config):
        assert config["services"][0]["apiUrl"] == "https://example.com/api/"

    def test_it_includes_the_authority(self, config):
        assert config["services"][0]["authority"] == "TEST_AUTHORITY"

    def test_it_disables_share_links(self, config):
        assert not config["services"][0]["enableShareLinks"]

    def test_it_includes_grant_token(self, config, pyramid_request):
        before = int(datetime.datetime.now().timestamp())

        grant_token = config["services"][0]["grantToken"]

        claims = jwt.decode(
            grant_token,
            algorithms=["HS256"],
            key="TEST_JWT_CLIENT_SECRET",
            audience="example.com",
        )
        assert claims["exp"] > before
        assert claims["iss"] == "TEST_JWT_CLIENT_ID"

        authority = pyramid_request.registry.settings["h_authority"]
        assert claims["sub"] == pyramid_request.lti_user.h_user.userid(authority)

        after = int(datetime.datetime.now().timestamp())
        assert before <= claims["nbf"] <= after

    def test_it_includes_the_group(self, config, context):
        groups = config["services"][0]["groups"]

        assert groups == [context.h_group.groupid.return_value]

    @pytest.mark.usefixtures("section_groups_on")
    def test_it_configures_the_client_to_fetch_the_groups_over_RPC(self, config):
        assert config["services"][0]["groups"] == "$rpc:requestGroups"

    @pytest.mark.usefixtures("provisioning_disabled")
    def test_it_is_empty_if_provisioning_feature_is_disabled(self, config):
        assert config == {}

    def test_it_is_mutable(self, config):
        config.update({"a_key": "a_value"})

        assert config["a_key"] == "a_value"

    @pytest.fixture
    def config(self, config):
        return config["hypothesisClient"]


class TestJSConfigRPCServer:
    """Unit tests for the "rpcServer" sub-dict of JSConfig."""

    def test_it(self, config):
        assert config == {"allowedOrigins": ["http://localhost:5000"]}

    @pytest.fixture
    def config(self, config):
        return config["rpcServer"]


class TestEnableCanvasOauth2RedirectErrorMode:
    def test_scope_error(self, js_config):
        js_config.enable_canvas_oauth2_redirect_error_mode(
            error_details="Technical error",
            is_scope_invalid=True,
            requested_scopes=["scope_a", "scope_b"],
        )

        config = js_config.asdict()

        assert config["mode"] == "canvas-oauth2-redirect-error"
        assert config["canvasOAuth2RedirectError"] == {
            "invalidScope": True,
            "errorDetails": "Technical error",
            "scopes": ["scope_a", "scope_b"],
        }

    def test_other_error(self, js_config):
        js_config.enable_canvas_oauth2_redirect_error_mode(error_details="Some error")

        config = js_config.asdict()

        assert config["mode"] == "canvas-oauth2-redirect-error"
        assert config["canvasOAuth2RedirectError"] == {
            "invalidScope": False,
            "errorDetails": "Some error",
            "scopes": [],
        }

    @pytest.fixture
    def js_config(self, context, pyramid_request):
        return JSConfig(context, pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.lti_user = None
        return pyramid_request

    @pytest.fixture
    def context(self):
        return mock.create_autospec(
            CanvasOAuth2RedirectResource, spec_set=True, instance=True
        )


pytestmark = pytest.mark.usefixtures("ai_getter", "grading_info_service", "h_api")


@pytest.fixture(autouse=True)
def BearerTokenSchema(patch):
    return patch("lms.resources._js_config.BearerTokenSchema")


@pytest.fixture
def bearer_token_schema(BearerTokenSchema):
    return BearerTokenSchema.return_value


@pytest.fixture
def js_config(context, pyramid_request):
    config = JSConfig(context, pyramid_request)
    config.enable_lti_launch_mode()
    return config


@pytest.fixture
def config(js_config):
    return js_config.asdict()


@pytest.fixture
def submission_params(config):
    return lambda: config["canvas"]["speedGrader"]["submissionParams"]


@pytest.fixture
def context():
    return mock.create_autospec(
        LTILaunchResource,
        spec_set=True,
        instance=True,
        h_group=mock.create_autospec(HGroup, instance=True, spec_set=True),
        is_canvas=True,
        canvas_sections_enabled=False,
    )


@pytest.fixture
def section_groups_on(context):
    context.canvas_sections_enabled = True


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.params.update(
        {
            "lis_result_sourcedid": "example_lis_result_sourcedid",
            "lis_outcome_service_url": "example_lis_outcome_service_url",
            "context_id": "test_course_id",
            "custom_canvas_course_id": "test_course_id",
            "custom_canvas_user_id": "test_user_id",
        }
    )
    return pyramid_request


@pytest.fixture
def provisioning_disabled(ai_getter):
    ai_getter.provisioning_enabled.return_value = False


@pytest.fixture(autouse=True)
def via_url(patch):
    return patch("lms.resources._js_config.via_url")


@pytest.fixture(autouse=True)
def GroupInfo(patch):
    group_info_class = patch("lms.resources._js_config.GroupInfo")
    group_info_class.columns.return_value = ["context_id", "custom_canvas_course_id"]
    return group_info_class
