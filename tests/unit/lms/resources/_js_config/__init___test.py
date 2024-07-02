from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any

from lms.models import Grouping, LTIParams
from lms.product.product import Routes
from lms.resources import LTILaunchResource, OAuth2RedirectResource
from lms.resources._js_config import JSConfig
from lms.security import Identity, Permissions
from lms.services import HAPIError
from lms.views.api.sync import APISyncSchema
from tests import factories
from tests.conftest import TEST_SETTINGS

pytestmark = pytest.mark.usefixtures(
    "grading_info_service",
    "grouping_service",
    "grouping_plugin",
    "grant_token_service",
    "h_api",
    "vitalsource_service",
    "jstor_service",
    "misc_plugin",
)


class TestFilePickerMode:
    def test_it(self, js_config, course):
        js_config.enable_file_picker_mode(
            sentinel.form_action, sentinel.form_fields, course
        )
        config = js_config.asdict()

        assert config == Any.dict.containing(
            {
                "mode": "content-item-selection",
                "filePicker": Any.dict.containing(
                    {
                        "formAction": sentinel.form_action,
                        "formFields": sentinel.form_fields,
                    }
                ),
            }
        )

    @pytest.mark.parametrize(
        "config_function,key",
        (
            ("blackboard_config", "blackboard"),
            ("canvas_config", "canvas"),
            ("canvas_studio_config", "canvasStudio"),
            ("google_files_config", "google"),
            ("microsoft_onedrive", "microsoftOneDrive"),
            ("vitalsource_config", "vitalSource"),
            ("jstor_config", "jstor"),
        ),
    )
    def test_it_adds_picker_config(
        self, js_config, pyramid_request, FilePickerConfig, config_function, key, course
    ):
        js_config.enable_file_picker_mode(
            sentinel.form_action, sentinel.form_fields, course
        )
        config = js_config.asdict()

        config_provider = getattr(FilePickerConfig, config_function)
        assert config["filePicker"][key] == config_provider.return_value
        config_provider.assert_called_once_with(
            pyramid_request, pyramid_request.lti_user.application_instance
        )

    def test_it_adds_product_info(self, js_config, course):
        js_config.enable_file_picker_mode(
            sentinel.form_action, sentinel.form_fields, course
        )

        assert js_config.asdict()["product"] == {
            "api": {},
            "settings": {"groupsEnabled": False},
        }

    def test_product_with_list_group_sets(self, js_config, pyramid_request, course):
        pyramid_request.product.route = Routes(oauth2_authorize="welcome")
        pyramid_request.product.settings.groups_enabled = True

        js_config.enable_file_picker_mode(
            sentinel.form_action, sentinel.form_fields, course
        )

        assert js_config.asdict()["product"] == {
            "api": {
                "listGroupSets": {
                    "authUrl": "http://example.com/welcome",
                    "path": "/api/courses/test_course_id/group_sets",
                }
            },
            "settings": {"groupsEnabled": True},
        }

    @pytest.fixture(autouse=True)
    def FilePickerConfig(self, patch):
        return patch("lms.resources._js_config.FilePickerConfig")


class TestEnableLTILaunchMode:
    def test_it(
        self,
        bearer_token_schema,
        grant_token_service,
        js_config,
        db_session,
        course,
        assignment,
        lti_user,
    ):
        lti_user.application_instance.organization = factories.Organization(
            public_id="us.lms.org.PUBLIC_ID"
        )
        db_session.flush()

        js_config.enable_lti_launch_mode(course, assignment)
        config = js_config.asdict()

        assert config == {
            "api": {
                "authToken": bearer_token_schema.authorization_param.return_value,
                "sync": Any(),
            },
            "canvas": {},
            "debug": {
                "tags": [Any.string.matching("^role:.*")],
                "values": {
                    "Organization ID": "us.lms.org.PUBLIC_ID",
                    "Application Instance ID": lti_user.application_instance.id,
                    "Assignment ID": assignment.id,
                    "Course ID": course.id,
                    "LTI version": "LTI-1p0",
                },
            },
            "product": {
                "api": {},
                "settings": {"groupsEnabled": False},
            },
            "dev": False,
            "editing": {
                "getConfig": {
                    "path": "/lti/reconfigure",
                    "data": Any.dict.containing(
                        {"authorization": "Bearer: token_value"}
                    ),
                },
            },
            "hypothesisClient": {
                "services": [
                    {
                        "allowFlagging": False,
                        "allowLeavingGroups": False,
                        "apiUrl": TEST_SETTINGS["h_api_url_public"],
                        "authority": TEST_SETTINGS["h_authority"],
                        "enableShareLinks": False,
                        "grantToken": grant_token_service.generate_token.return_value,
                        "groups": Any(),
                    }
                ],
                "annotationMetadata": {
                    "lms": {
                        "guid": lti_user.application_instance.tool_consumer_instance_guid,
                        "assignment": {
                            "resource_link_id": assignment.resource_link_id,
                        },
                    }
                },
            },
            "mode": "basic-lti-launch",
            "rpcServer": {"allowedOrigins": ["http://localhost:5000"]},
        }

    @pytest.mark.usefixtures("grouping_plugin")
    def test_configures_the_client_with_course_group(
        self, js_config, grouping_service, course, assignment
    ):
        grouping_service.get_launch_grouping_type.return_value = Grouping.Type.COURSE

        js_config.enable_lti_launch_mode(course, assignment)
        config = js_config.asdict()

        assert config["hypothesisClient"]["services"][0]["groups"] == [
            Any.string.matching("^group:.*@lms.hypothes.is")
        ]
        assert not config["api"]["sync"]

    @pytest.mark.usefixtures("grouping_plugin")
    @pytest.mark.parametrize(
        "grouping_type", [Grouping.Type.SECTION, Grouping.Type.GROUP]
    )
    def test_configures_the_client_to_fetch_the_groups_over_RPC(
        self,
        js_config,
        grouping_service,
        grouping_type,
        course,
        assignment,
        grouping_plugin,
        pyramid_request,
    ):
        grouping_service.get_launch_grouping_type.return_value = grouping_type
        pyramid_request.lti_params["context_id"] = "CONTEXT_ID"
        pyramid_request.params["learner_canvas_user_id"] = "CANVAS_USER_ID"
        grouping_service.get_launch_grouping_type.return_value = grouping_type
        grouping_plugin.get_group_set_id.return_value = "GROUP_SET_ID"

        js_config.enable_lti_launch_mode(course, assignment)
        config = js_config.asdict()

        assert (
            config["hypothesisClient"]["services"][0]["groups"] == "$rpc:requestGroups"
        )
        sync_config = config["api"]["sync"]
        assert sync_config == {
            "authUrl": "http://example.com/welcome",
            "path": "/api/sync",
            "data": {
                "resource_link_id": assignment.resource_link_id,
                "context_id": "CONTEXT_ID",
                "group_set_id": "GROUP_SET_ID",
                "group_info": {
                    "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
                    "tool_consumer_info_product_family_code": "whiteboard",
                    "context_id": "CONTEXT_ID",
                    "context_title": "A context title",
                    "context_label": "A context label",
                    "custom_canvas_course_id": "test_course_id",
                },
                # This is only actually true for Canvas, but we do it for all
                # LMS products at the moment
                "gradingStudentId": "CANVAS_USER_ID",
            },
        }

        # Confirm we pass the schema for the sync end-point
        APISyncSchema(pyramid_request).load(sync_config["data"])


class TestAddDocumentURL:
    """Unit tests for JSConfig.add_document_url()."""

    def test_it_adds_the_via_url(self, js_config, pyramid_request, via_url):
        js_config.add_document_url("example_document_url")

        via_url.assert_called_once_with(pyramid_request, "example_document_url")
        assert js_config.asdict()["viaUrl"] == via_url.return_value

    @pytest.mark.parametrize(
        "url,via_url",
        [
            (
                "blackboard://content-resource/xyz123",
                {
                    "authUrl": "http://example.com/api/blackboard/oauth/authorize",
                    "path": "/api/blackboard/courses/test_course_id/via_url?document_url=blackboard%3A%2F%2Fcontent-resource%2Fxyz123",
                },
            ),
            (
                "canvas://file/course/COURSE/file_id/FILE",
                {
                    "authUrl": "http://example.com/api/canvas/oauth/authorize",
                    "path": "/api/canvas/assignments/TEST_RESOURCE_LINK_ID/via_url",
                },
            ),
            (
                "canvas://page/course/COURSE/page_id/PAGE",
                {
                    "authUrl": "http://example.com/api/canvas/oauth/authorize",
                    "path": "/api/canvas/pages/via_url",
                },
            ),
            (
                "d2l://file/course/125/file_id/100",
                {
                    "authUrl": "http://example.com/api/d2l/oauth/authorize",
                    "path": "/api/d2l/courses/test_course_id/via_url?document_url=d2l%3A%2F%2Ffile%2Fcourse%2F125%2Ffile_id%2F100",
                },
            ),
            (
                "moodle://file/course/125/file_id/100",
                {
                    "authUrl": None,
                    "path": "/api/moodle/courses/test_course_id/via_url?document_url=moodle%3A%2F%2Ffile%2Fcourse%2F125%2Ffile_id%2F100",
                },
            ),
            (
                "moodle://page/course/125/page_id/100",
                {
                    "authUrl": None,
                    "path": "/api/moodle/pages/via_url",
                },
            ),
        ],
    )
    def test_it_adds_the_viaUrl_api_config(self, url, via_url, js_config):
        js_config.add_document_url(url)

        assert js_config.asdict()["api"]["viaUrl"] == via_url

    @pytest.mark.parametrize("is_admin", (True, False))
    def test_canvas_studio_adds_config(
        self, js_config, canvas_studio_service, is_admin
    ):
        canvas_studio_service.is_admin.return_value = is_admin

        document_url = "canvas-studio://media/media_id"
        js_config.add_document_url(document_url)

        expected_auth_url = None
        if is_admin:
            expected_auth_url = "http://example.com/api/canvas_studio/oauth/authorize"

        assert js_config.asdict()["api"]["viaUrl"] == {
            "authUrl": expected_auth_url,
            "path": "/api/canvas_studio/via_url",
        }

    def test_vitalsource_sets_config_with_sso(
        self, js_config, pyramid_request, vitalsource_service
    ):
        document_url = "vitalsource://book/bookID/book-id/cfi//abc"
        vitalsource_service.sso_enabled = True
        vitalsource_service.get_user_reference.return_value = "a_string"

        js_config.add_document_url(document_url)

        vitalsource_service.get_user_reference.assert_called_once_with(
            pyramid_request.lti_params
        )

        proxy_api_call = Any.url.matching(
            "http://example.com/api/vitalsource/launch_url"
        ).with_query(
            {
                "user_reference": vitalsource_service.get_user_reference.return_value,
                "document_url": document_url,
            }
        )
        assert js_config.asdict()["api"]["viaUrl"] == {"path": proxy_api_call}

    def test_vitalsource_sets_config_without_sso(self, js_config, vitalsource_service):
        document_url = "vitalsource://book/bookID/book-id/cfi//abc"
        vitalsource_service.sso_enabled = False

        js_config.add_document_url(document_url)

        vitalsource_service.get_book_reader_url.assert_called_with(
            document_url=document_url
        )
        assert (
            js_config.asdict()["viaUrl"]
            == vitalsource_service.get_book_reader_url.return_value
        )

    @pytest.mark.parametrize("assignment_has_content_range", [True, False])
    def test_vitalsource_sets_content_focus(
        self,
        js_config,
        vitalsource_service,
        course,
        assignment,
        assignment_has_content_range,
    ):
        document_url = "vitalsource://book/bookID/book-id/page/20?end_page=30"
        if assignment_has_content_range:
            focus_config_from_url = {"page": "20-30"}
        else:
            focus_config_from_url = None

        vitalsource_service.get_client_focus_config.return_value = focus_config_from_url

        # `add_document_url` fetches the content range, `enable_lti_launch_mode`
        # adds it to the dict under `hypothesisClient`.
        js_config.add_document_url(document_url)
        js_config.enable_lti_launch_mode(course, assignment)

        client_config = js_config.asdict()["hypothesisClient"]
        focus_config = client_config.get("focus", {})

        if assignment_has_content_range:
            assert focus_config["page"] == "20-30"
        else:
            assert "page" not in focus_config

    def test_jstor_sets_config(self, js_config, jstor_service, pyramid_request):
        jstor_url = "jstor://DOI"

        js_config.add_document_url(jstor_url)

        jstor_service.via_url.assert_called_with(pyramid_request, jstor_url)
        assert js_config.asdict()["contentBanner"] == {
            "source": "jstor",
            "itemId": "DOI",
        }
        assert js_config.asdict()["viaUrl"] == jstor_service.via_url.return_value


class TestAddCanvasSpeedgraderSettings:
    @pytest.mark.parametrize("group_set", (sentinel.group_set, None))
    def test_it(self, js_config, pyramid_request, course, assignment, group_set):
        pyramid_request.feature.return_value = False
        if group_set:
            pyramid_request.params["group_set"] = group_set

        js_config.add_canvas_speedgrader_settings(sentinel.document_url)

        # Ensure `hypothesisClient` is added to config.
        js_config.enable_lti_launch_mode(course, assignment)

        config = js_config.asdict()
        assert config["canvas"]["speedGrader"]["submissionParams"] == {
            "h_username": pyramid_request.lti_user.h_user.username,
            "group_set": group_set,
            "document_url": sentinel.document_url,
            "resource_link_id": pyramid_request.params["resource_link_id"],
            "lis_result_sourcedid": pyramid_request.lti_params["lis_result_sourcedid"],
            "lis_outcome_service_url": pyramid_request.lti_params[
                "lis_outcome_service_url"
            ],
            "learner_canvas_user_id": pyramid_request.lti_params[
                "custom_canvas_user_id"
            ],
        }
        assert config["hypothesisClient"]["reportActivity"] == {
            "method": "reportActivity",
            "events": ["create", "update"],
        }


class TestEnableClientFeature:
    def test_it(self, js_config, course, assignment):
        js_config.enable_client_feature("feature_a")
        js_config.enable_client_feature("feature_b")

        # Enable feature a second time. This should be a no-op.
        js_config.enable_client_feature("feature_a")

        # Ensure `hypothesisClient` is added to config.
        js_config.enable_lti_launch_mode(course, assignment)
        config = js_config.asdict()

        assert config["hypothesisClient"]["features"] == [
            "feature_a",
            "feature_b",
        ]


class TestInstructorToolbar:
    @pytest.mark.parametrize(
        "enable_editing, enable_grading", [(True, False), (False, True)]
    )
    def test_instructor_toolbar(
        self,
        js_config,
        pyramid_request,
        enable_editing,
        enable_grading,
        misc_plugin,
        application_instance,
    ):
        if enable_grading:
            js_config.enable_toolbar_grading(sentinel.students, sentinel.score_maximum)

        if enable_editing:
            js_config.enable_toolbar_editing()

        expected = {
            "courseName": pyramid_request.lti_params["context_title"],
            "assignmentName": pyramid_request.lti_params["resource_link_title"],
        }

        if enable_editing:
            expected["editingEnabled"] = enable_editing

        if enable_grading:
            misc_plugin.accept_grading_comments.assert_called_once_with(
                application_instance
            )
            expected["gradingEnabled"] = enable_grading
            expected["acceptGradingComments"] = (
                misc_plugin.accept_grading_comments.return_value
            )
            expected["students"] = sentinel.students
            expected["scoreMaximum"] = sentinel.score_maximum

        assert js_config.asdict()["instructorToolbar"] == expected


class TestSetFocusedUser:
    def test_it_sets_the_focused_user_if_theres_a_focused_user_param(
        self, h_api, js_config
    ):
        js_config.set_focused_user(sentinel.focused_user)

        h_api.get_user.assert_called_once_with(sentinel.focused_user)
        assert js_config.asdict()["hypothesisClient"]["focus"] == {
            "user": {
                "username": sentinel.focused_user,
                "displayName": h_api.get_user.return_value.display_name,
            },
        }

    def test_display_name_falls_back_to_a_default_value(self, h_api, js_config):
        h_api.get_user.side_effect = HAPIError()

        js_config.set_focused_user(sentinel.focused_user)

        assert (
            js_config.asdict()["hypothesisClient"]["focus"]["user"]["displayName"]
            == "(Couldn't fetch student name)"
        )

    @pytest.fixture
    def js_config(self, js_config, assignment, course):
        # `set_focused_user` needs the `hypothesisClient` section to exist
        js_config.enable_lti_launch_mode(course, assignment)

        return js_config


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


class TestJSConfigDebug:
    """Unit tests for the "debug" sub-dict of JSConfig."""

    @pytest.mark.usefixtures("user_is_learner")
    def test_it_contains_debugging_info_about_the_users_role(self, config):
        assert "role:learner" in config["tags"]

    @pytest.fixture
    def config(self, config):
        return config["debug"]


class TestEnableOAuth2RedirectErrorMode:
    def test_it(self, js_config):
        js_config.enable_oauth2_redirect_error_mode(
            "auth_route",
            sentinel.error_code,
            sentinel.error_details,
            sentinel.canvas_scopes,
        )
        config = js_config.asdict()

        assert config["mode"] == JSConfig.Mode.OAUTH2_REDIRECT_ERROR
        assert config["OAuth2RedirectError"] == {
            "authUrl": "http://example.com/auth?authorization=Bearer%3A+token_value",
            "errorCode": sentinel.error_code,
            "errorDetails": sentinel.error_details,
            "canvasScopes": sentinel.canvas_scopes,
        }

    @pytest.mark.usefixtures("with_no_user")
    def test_if_theres_no_authenticated_user_it_sets_authUrl_to_None(self, js_config):
        js_config.enable_oauth2_redirect_error_mode(auth_route="auth_route")
        config = js_config.asdict()

        assert config["OAuth2RedirectError"]["authUrl"] is None

    def test_it_omits_errorDetails_if_no_error_details_argument_is_given(
        self, js_config
    ):
        js_config.enable_oauth2_redirect_error_mode(auth_route="auth_route")
        config = js_config.asdict()

        assert "errorDetails" not in config["OAuth2RedirectError"]

    def test_canvas_scopes_defaults_to_an_empty_list(self, js_config):
        js_config.enable_oauth2_redirect_error_mode(auth_route="auth_route")
        config = js_config.asdict()

        assert config["OAuth2RedirectError"]["canvasScopes"] == []

    @pytest.fixture
    def context(self):
        return create_autospec(OAuth2RedirectResource, spec_set=True, instance=True)

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("auth_route", "/auth")

    @pytest.fixture
    def with_no_user(self, pyramid_request):
        pyramid_request.lti_user = None


class TestAddDeepLinkingAPI:
    def test_it_adds_deep_linking_v11(self, js_config, pyramid_request):
        pyramid_request.lti_params.update(
            {
                "content_item_return_url": sentinel.content_item_return_url,
                "data": sentinel.data,
            }
        )

        js_config.add_deep_linking_api()

        config = js_config.asdict()
        assert config["filePicker"]["deepLinkingAPI"] == {
            "path": "/lti/1.1/deep_linking/form_fields",
            "data": {
                "content_item_return_url": sentinel.content_item_return_url,
                "context_id": pyramid_request.lti_params["context_id"],
                "opaque_data_lti11": sentinel.data,
            },
        }

    @pytest.mark.usefixtures("lti_v13_application_instance")
    def test_it_adds_deep_linking_v13(self, js_config, pyramid_request):
        pyramid_request.lti_params.update(
            {
                "deep_linking_settings": sentinel.deep_linking_settings,
                "content_item_return_url": sentinel.content_item_return_url,
            }
        )

        js_config.add_deep_linking_api()

        config = js_config.asdict()
        assert config["filePicker"]["deepLinkingAPI"] == {
            "path": "/lti/1.3/deep_linking/form_fields",
            "data": {
                "content_item_return_url": sentinel.content_item_return_url,
                "opaque_data_lti13": sentinel.deep_linking_settings,
                "context_id": pyramid_request.lti_params["context_id"],
            },
        }


class TestEnableErrorDialogMode:
    def test_it(self, js_config, LTIEvent, EventService, pyramid_request):
        js_config.enable_error_dialog_mode(
            error_code=sentinel.error_code,
            error_details={"more": "details"},
            message=sentinel.message,
        )
        config = js_config.asdict()

        assert config["mode"] == JSConfig.Mode.ERROR_DIALOG
        assert config["errorDialog"] == {
            "errorCode": sentinel.error_code,
            "errorDetails": {"more": "details"},
            "errorMessage": sentinel.message,
        }
        LTIEvent.from_request.assert_called_once_with(
            request=pyramid_request,
            type_=LTIEvent.Type.ERROR_CODE,
            data={"code": sentinel.error_code, "more": "details"},
        )
        EventService.queue_event.assert_called_once_with(
            LTIEvent.from_request.return_value
        )

    def test_it_omits_errorDetails_if_no_error_details_argument_is_given(
        self, js_config
    ):
        js_config.enable_error_dialog_mode(sentinel.error_code)
        config = js_config.asdict()

        assert "errorDetails" not in config["errorDialog"]

    @pytest.fixture
    def context(self):
        return create_autospec(OAuth2RedirectResource, spec_set=True, instance=True)

    @pytest.fixture(autouse=True)
    def EventService(self, patch):
        return patch("lms.resources._js_config.EventService")

    @pytest.fixture(autouse=True)
    def LTIEvent(self, patch):
        return patch("lms.resources._js_config.LTIEvent")


class TestEnableDashboardMode:
    def test_it(self, js_config, lti_user):
        js_config.enable_dashboard_mode()
        config = js_config.asdict()

        assert config["mode"] == JSConfig.Mode.DASHBOARD
        assert config["dashboard"] == {
            "user": {"display_name": lti_user.display_name, "is_staff": False},
            "routes": {
                "assignment": "/api/dashboard/assignments/:assignment_id",
                "assignment_stats": "/api/dashboard/assignments/:assignment_id/stats",
                "course": "/api/dashboard/courses/:course_id",
                "course_assignment_stats": "/api/dashboard/courses/:course_id/assignments/stats",
                "organization_courses": "/api/dashboard/organizations/:organization_public_id/courses",
                "courses": "/api/dashboard/courses",
                "assignments": "/api/dashboard/assignments",
                "students": "/api/dashboard/students",
            },
        }

    def test_user_when_staff(self, js_config, pyramid_request_staff_member, context):
        js_config = JSConfig(context, pyramid_request_staff_member)
        js_config.enable_dashboard_mode()
        config = js_config.asdict()

        assert config["dashboard"]["user"] == {
            "is_staff": True,
            "display_name": "staff@example.com",
        }

    @pytest.fixture
    def pyramid_request_staff_member(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy(
            userid="staff@example.com",
            identity=Identity("staff@example.com", [Permissions.STAFF]),
        )
        pyramid_request.lti_user = None
        return pyramid_request


class TestEnableInstructorDashboardEntryPoint:
    def test_it(self, js_config, db_session):
        assignment = factories.Assignment()
        db_session.flush()  # force assignment to have an ID

        js_config.enable_instructor_dashboard_entry_point(assignment)
        config = js_config.asdict()

        assert config["hypothesisClient"]["dashboard"] == {
            "showEntryPoint": True,
            "authTokenRPCMethod": "requestAuthToken",
            "entryPointURL": f"http://example.com/dashboard/launch/assignments/{assignment.id}",
            "authFieldName": "authorization",
        }


@pytest.fixture(autouse=True)
def BearerTokenSchema(patch):
    BearerTokenSchema = patch("lms.resources._js_config.BearerTokenSchema")
    BearerTokenSchema.return_value.authorization_param.return_value = (
        "Bearer: token_value"
    )
    return BearerTokenSchema


@pytest.fixture
def bearer_token_schema(BearerTokenSchema):
    return BearerTokenSchema.return_value


@pytest.fixture
def js_config(context, pyramid_request):
    return JSConfig(context, pyramid_request)


@pytest.fixture
def config(js_config):
    return js_config.asdict()


@pytest.fixture
def context():
    return create_autospec(LTILaunchResource, spec_set=True, instance=True)


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
    pyramid_request.lti_params = LTIParams.from_request(pyramid_request)
    pyramid_request.product.route = Routes(oauth2_authorize="welcome")
    return pyramid_request


@pytest.fixture
def assignment():
    return factories.Assignment()


@pytest.fixture
def course():
    return factories.Course()


@pytest.fixture(autouse=True)
def via_url(patch):
    return patch("lms.resources._js_config.via_url")
