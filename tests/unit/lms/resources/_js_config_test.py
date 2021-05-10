from unittest import mock

import pytest
from h_matchers import Any

from lms.models import GradingInfo, HGroup
from lms.resources import LTILaunchResource, OAuth2RedirectResource
from lms.resources._js_config import JSConfig
from lms.services import ConsumerKeyError, HAPIError

pytestmark = pytest.mark.usefixtures(
    "application_instance_service",
    "grading_info_service",
    "grant_token_service",
    "h_api",
    "vitalsource_service",
)


class TestEnableContentItemSelectionMode:
    @pytest.mark.usefixtures("blackboard_files_enabled")
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
            "blackboard": {
                "enabled": True,
                "listFiles": {
                    "authUrl": "http://example.com/api/blackboard/oauth/authorize",
                    "path": "/api/blackboard/courses/test_course_id/files",
                },
            },
            "canvas": {
                "enabled": True,
                "groupsEnabled": False,
                "ltiLaunchUrl": "http://example.com/lti_launches",
                "listFiles": {
                    "authUrl": "http://example.com/api/canvas/oauth/authorize",
                    "path": "/api/canvas/courses/test_course_id/files",
                },
                "listGroupCategories": {
                    "authUrl": "http://example.com/api/canvas/oauth/authorize",
                    "path": "/api/canvas/courses/test_course_id/group_categories",
                },
            },
            "vitalSource": {
                "enabled": False,
            },
        }

    def test_google_picker_origin_falls_back_to_lms_url_if_theres_no_custom_canvas_api_domain(
        self, application_instance_service, context, js_config
    ):
        context.custom_canvas_api_domain = None

        js_config.enable_content_item_selection_mode(
            mock.sentinel.form_action, mock.sentinel.form_fields
        )

        assert (
            js_config.asdict()["filePicker"]["google"]["origin"]
            == application_instance_service.get.return_value.lms_url
        )

    def test_it_doesnt_enable_the_blackboard_file_picker_if_the_feature_flag_is_off(
        self, js_config
    ):
        js_config.enable_content_item_selection_mode(
            mock.sentinel.form_action, mock.sentinel.form_fields
        )

        assert not js_config.asdict()["filePicker"]["blackboard"]["enabled"]

    def test_it_doesnt_enable_the_canvas_file_picker_if_the_lms_isnt_Canvas(
        self, context, js_config
    ):
        context.is_canvas = False

        js_config.enable_content_item_selection_mode(
            mock.sentinel.form_action, mock.sentinel.form_fields
        )

        self.assert_canvas_file_picker_not_enabled(js_config)

    def test_it_doesnt_enable_the_canvas_file_picker_if_we_dont_have_a_developer_key(
        self, application_instance_service, js_config
    ):
        application_instance_service.get.return_value.developer_key = None

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

    def test_it_enables_vitalsource_picker_if_feature_enabled(
        self, pyramid_request, js_config
    ):
        pyramid_request.feature = lambda feature: feature == "vitalsource"

        js_config.enable_content_item_selection_mode(
            mock.sentinel.form_action, mock.sentinel.form_fields
        )

        assert js_config.asdict()["filePicker"]["vitalSource"]["enabled"]

    def test_it_raises_if_theres_no_ApplicationInstance(
        self, application_instance_service, context, js_config
    ):
        context.custom_canvas_api_domain = None
        application_instance_service.get.side_effect = ConsumerKeyError

        with pytest.raises(ConsumerKeyError):
            js_config.enable_content_item_selection_mode(
                mock.sentinel.form_action, mock.sentinel.form_fields
            )

    def assert_canvas_file_picker_not_enabled(self, js_config):
        assert not js_config.asdict()["filePicker"]["canvas"]["enabled"]
        assert "courseId" not in js_config.asdict()

    @pytest.fixture
    def blackboard_files_enabled(self, application_instance_service):
        application_instance = application_instance_service.get.return_value
        application_instance.settings.set("blackboard", "files_enabled", True)


class TestEnableLTILaunchMode:
    def test_it(self, bearer_token_schema, context, grant_token_service, js_config):
        js_config.enable_lti_launch_mode()

        assert js_config.asdict() == {
            "api": {
                "authToken": bearer_token_schema.authorization_param.return_value,
                "sync": None,
            },
            "canvas": {},
            "debug": {"tags": [Any.string.matching("^role:.*")]},
            "dev": False,
            "hypothesisClient": {
                "services": [
                    {
                        "allowLeavingGroups": False,
                        "apiUrl": "https://example.com/api/",
                        "authority": "TEST_AUTHORITY",
                        "enableShareLinks": False,
                        "grantToken": grant_token_service.generate_token.return_value,
                        "groups": [context.h_group.groupid.return_value],
                    }
                ]
            },
            "mode": "basic-lti-launch",
            "rpcServer": {"allowedOrigins": ["http://localhost:5000"]},
        }

    def test_it_raises_if_theres_no_ApplicationInstance(
        self, application_instance_service, js_config
    ):
        application_instance_service.get.side_effect = ConsumerKeyError

        with pytest.raises(ConsumerKeyError):
            js_config.enable_lti_launch_mode()


class TestAddCanvasFileID:
    """Unit tests for JSConfig.add_canvas_file_id()."""

    def test_it_adds_the_viaUrl_api_config(self, js_config):
        js_config.add_canvas_file_id(
            "example_canvas_course_id", "example_canvas_file_id"
        )

        assert js_config.asdict()["api"]["viaUrl"] == {
            "authUrl": "http://example.com/api/canvas/oauth/authorize",
            "path": "/api/canvas/courses/example_canvas_course_id/files/example_canvas_file_id/via_url",
        }

    def test_it_sets_the_canvas_file_id(self, js_config, submission_params):
        js_config.add_canvas_file_id(
            "example_canvas_course_id", "example_canvas_file_id"
        )

        assert submission_params()["canvas_file_id"] == "example_canvas_file_id"


class TestAddDocumentURL:
    """Unit tests for JSConfig.add_document_url()."""

    def test_it_adds_the_via_url(self, js_config, pyramid_request, via_url):
        js_config.add_document_url("example_document_url")

        via_url.assert_called_once_with(pyramid_request, "example_document_url")
        assert js_config.asdict()["viaUrl"] == via_url.return_value

    def test_it_adds_the_viaUrl_api_config_for_Blackboard_documents(self, js_config):
        js_config.add_document_url("blackboard://content-resource/xyz123")

        assert js_config.asdict()["api"]["viaUrl"] == {
            "authUrl": "http://example.com/api/blackboard/oauth/authorize",
            "path": "/api/blackboard/courses/test_course_id/files/xyz123/via_url",
        }

    def test_it_sets_the_document_url(self, js_config, submission_params):
        js_config.add_document_url("example_document_url")

        assert submission_params()["document_url"] == "example_document_url"


class TestAddVitalsourceLaunchConfig:
    """Unit tests for JSConfig.add_vitalsource_launch_config()."""

    def test_it_sets_vitalsource_config(
        self, js_config, pyramid_request, vitalsource_service
    ):
        js_config.add_vitalsource_launch_config("book-id", "/abc")

        vitalsource_service.get_launch_params.assert_called_with(
            "book-id", "/abc", pyramid_request.lti_user
        )
        assert js_config.asdict()["vitalSource"] == {
            "launchUrl": mock.sentinel.launch_url,
            "launchParams": mock.sentinel.launch_params,
        }

    def test_it_sets_submission_params(self, js_config, submission_params):
        js_config.add_vitalsource_launch_config("book-id", "/abc")

        assert submission_params() == Any.dict.containing(
            {
                "vitalsource_book_id": "book-id",
                "vitalsource_cfi": "/abc",
            }
        )

    @pytest.fixture
    def vitalsource_service(self, vitalsource_service):
        vitalsource_service.get_launch_params.return_value = (
            mock.sentinel.launch_url,
            mock.sentinel.launch_params,
        )
        return vitalsource_service


class TestAddCanvasFileIDAddDocumentURLCommon:
    """Tests common to both add_canvas_file_id() and add_document_url()."""

    def test_it_sets_the_canvas_submission_params(
        self, pyramid_request, method_caller, submission_params
    ):
        method_caller()

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
        self, context, method_caller, js_config
    ):
        context.is_canvas = False

        method_caller()

        assert "speedGrader" not in js_config.asdict()["canvas"]

    def test_it_doesnt_set_the_speedGrader_settings_if_theres_no_lis_result_sourcedid(
        self, method_caller, js_config, pyramid_request
    ):
        del pyramid_request.params["lis_result_sourcedid"]

        method_caller()

        assert "speedGrader" not in js_config.asdict()["canvas"]

    def test_it_doesnt_set_the_speedGrader_settings_if_theres_no_lis_outcome_service_url(
        self, method_caller, js_config, pyramid_request
    ):
        del pyramid_request.params["lis_outcome_service_url"]

        method_caller()

        assert "speedGrader" not in js_config.asdict()["canvas"]

    @pytest.fixture(
        params=[
            {
                "method": "add_canvas_file_id",
                "args": ["example_canvas_course_id", "example_canvas_file_id"],
            },
            {"method": "add_document_url", "args": ["example_document_url"]},
        ]
    )
    def method_caller(self, js_config, request):
        """Return a function that calls the method-under-test with default args."""

        def method_caller():
            return getattr(js_config, request.param["method"])(*request.param["args"])

        return method_caller


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
        # maybe_set_focused_user() doesn't work properly unless
        # enable_lti_launch_mode() has been called first because it depends on
        # enable_lti_launch_mode() having inserted the "hypothesisClient"
        # section into the config.
        js_config.enable_lti_launch_mode()

        js_config.maybe_set_focused_user()

        assert "focus" not in js_config.asdict()["hypothesisClient"]

    def test_it_sets_the_focused_user_if_theres_a_focused_user_param(
        self, h_api, js_config
    ):
        # maybe_set_focused_user() doesn't work properly unless
        # enable_lti_launch_mode() has been called first because it depends on
        # enable_lti_launch_mode() having inserted the "hypothesisClient"
        # section into the config.
        js_config.enable_lti_launch_mode()

        js_config.maybe_set_focused_user()

        # It gets the display name from the h API.
        h_api.get_user.assert_called_once_with("example_h_username")
        # It sets the focused user.
        assert js_config.asdict()["hypothesisClient"]["focus"] == {
            "user": {
                "username": "example_h_username",
                "displayName": h_api.get_user.return_value.display_name,
            },
        }

    def test_display_name_falls_back_to_a_default_value(self, h_api, js_config):
        h_api.get_user.side_effect = HAPIError()
        # maybe_set_focused_user() doesn't work properly unless
        # enable_lti_launch_mode() has been called first because it depends on
        # enable_lti_launch_mode() having inserted the "hypothesisClient"
        # section into the config.
        js_config.enable_lti_launch_mode()

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
            "authUrl": "http://example.com/api/canvas/oauth/authorize",
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
            "canvas_user_id": "test_learner_canvas_user_id",
        }

    def test_its_None_if_section_groups_isnt_enabled(self, sync):
        assert sync is None

    @pytest.fixture
    def sync(self, config, js_config):
        # Call enable_lti_launch_mode() so that the api.sync section gets
        # inserted into the config.
        js_config.enable_lti_launch_mode()

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

    def test_it_includes_grant_token(
        self, config, pyramid_request, grant_token_service
    ):
        grant_token_service.generate_token.assert_called_with(
            pyramid_request.lti_user.h_user
        )
        grant_token = config["services"][0]["grantToken"]
        assert grant_token == grant_token_service.generate_token.return_value

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
    def config(self, config, js_config):
        # Call enable_lti_launch_mode() so that the "hypothesisClient" section
        # gets inserted into the config.
        js_config.enable_lti_launch_mode()

        return config["hypothesisClient"]


class TestJSConfigRPCServer:
    """Unit tests for the "rpcServer" sub-dict of JSConfig."""

    def test_it(self, config):
        assert config == {"allowedOrigins": ["http://localhost:5000"]}

    @pytest.fixture
    def config(self, config, js_config):
        # Call enable_lti_launch_mode() so that the "rpcServer" section gets
        # inserted into the config.
        js_config.enable_lti_launch_mode()

        return config["rpcServer"]


class TestEnableCanvasOauth2RedirectErrorMode:
    def test_scope_error(self, js_config):
        js_config.enable_canvas_oauth2_redirect_error_mode(
            auth_url=None,
            error_details="Technical error",
            is_scope_invalid=True,
            requested_scopes=["scope_a", "scope_b"],
        )

        config = js_config.asdict()

        assert config["mode"] == "canvas-oauth2-redirect-error"
        assert config["canvasOAuth2RedirectError"] == {
            "authUrl": None,
            "invalidScope": True,
            "errorDetails": "Technical error",
            "scopes": ["scope_a", "scope_b"],
        }

    def test_other_error(self, js_config):
        auth_url = "https://lms.hypothes.is/auth/url"
        js_config.enable_canvas_oauth2_redirect_error_mode(
            auth_url=auth_url, error_details="Some error"
        )

        config = js_config.asdict()

        assert config["mode"] == "canvas-oauth2-redirect-error"
        assert config["canvasOAuth2RedirectError"] == {
            "authUrl": auth_url,
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
            OAuth2RedirectResource, spec_set=True, instance=True
        )


@pytest.fixture(autouse=True)
def BearerTokenSchema(patch):
    return patch("lms.resources._js_config.BearerTokenSchema")


@pytest.fixture
def bearer_token_schema(BearerTokenSchema):
    return BearerTokenSchema.return_value


@pytest.fixture
def js_config(context, pyramid_request):
    config = JSConfig(context, pyramid_request)
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
def provisioning_disabled(application_instance_service):
    application_instance_service.get.return_value.provisioning = False


@pytest.fixture(autouse=True)
def via_url(patch):
    return patch("lms.resources._js_config.via_url")


@pytest.fixture(autouse=True)
def GroupInfo(patch):
    group_info_class = patch("lms.resources._js_config.GroupInfo")
    group_info_class.columns.return_value = ["context_id", "custom_canvas_course_id"]
    return group_info_class
