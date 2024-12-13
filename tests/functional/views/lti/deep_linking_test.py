import json
import time
from datetime import timedelta

import oauthlib.common
import oauthlib.oauth1
import pytest
from h_matchers import Any

from lms.resources._js_config import JSConfig
from lms.services.jwt import JWTService
from lms.services.lti_user import LTIUserService
from tests import factories
from tests.conftest import TEST_SETTINGS


class TestDeepLinkingLaunch:
    def test_basic_lti_launch_canvas_deep_linking_url(
        self,
        do_deep_link_launch,
        lti_params,
        application_instance,
        get_client_config,
        environ,
    ):
        response = do_deep_link_launch(post_params=lti_params, status=200)

        js_config = get_client_config(response)
        assert js_config["mode"] == JSConfig.Mode.FILE_PICKER
        assert js_config["filePicker"] == {
            "autoGradingEnabled": True,
            "blackboard": {"enabled": None},
            "canvas": {
                "enabled": None,
                "foldersEnabled": None,
                "listFiles": {
                    "authUrl": "http://localhost/api/canvas/oauth/authorize",
                    "path": "/api/canvas/courses/None/files",
                },
                "pagesEnabled": None,
            },
            "canvasStudio": {"enabled": False},
            "d2l": {"enabled": False},
            "deepLinkingAPI": {
                "data": {
                    "content_item_return_url": "https://apps.imsglobal.org/lti/cert/tp/tp_return.php/basic-lti-launch-request",
                    "context_id": "con-182",
                    "opaque_data_lti11": None,
                },
                "path": "/lti/1.1/deep_linking/form_fields",
            },
            "formAction": "https://apps.imsglobal.org/lti/cert/tp/tp_return.php/basic-lti-launch-request",
            "formFields": {
                "lti_message_type": "ContentItemSelection",
                "lti_version": "LTI-1p0",
            },
            "google": {
                "clientId": environ["GOOGLE_CLIENT_ID"],
                "developerKey": environ["GOOGLE_DEVELOPER_KEY"],
                "enabled": True,
                "origin": application_instance.lms_url,
            },
            "jstor": {"enabled": False},
            "ltiLaunchUrl": "http://localhost/lti_launches",
            "microsoftOneDrive": {
                "clientId": environ["ONEDRIVE_CLIENT_ID"],
                "enabled": True,
                "redirectURI": "http://localhost/onedrive/filepicker/redirect",
            },
            "moodle": {"enabled": None, "pagesEnabled": None},
            "promptForTitle": True,
            "vitalSource": {"enabled": False},
            "youtube": {"enabled": Any()},
        }


class TestDeepLinkingFieldsViews:
    def test_file_picker_to_form_fields_v11(
        self, app, authorization_param, application_instance
    ):
        response = app.post_json(
            "/lti/1.1/deep_linking/form_fields",
            params={
                "content_item_return_url": "https://apps.imsglobal.org/lti/cert/tp/tp_return.php/basic-lti-launch-request",
                "content": {"type": "url", "url": "https://example.com"},
            },
            headers={"Authorization": f"Bearer {authorization_param}"},
            status=200,
        )

        response_json = response.json
        content_items = response_json.pop(
            "content_items"
        )  # We'll assert this separately
        assert response_json == {
            "oauth_version": "1.0",
            "oauth_nonce": Any.string(),
            "oauth_timestamp": Any.string(),
            "oauth_consumer_key": application_instance.consumer_key,
            "oauth_signature_method": "HMAC-SHA1",
            "lti_message_type": "ContentItemSelection",
            "lti_version": "LTI-1p0",
            "oauth_signature": Any.string(),
        }
        assert json.loads(content_items) == {
            "@context": "http://purl.imsglobal.org/ctx/lti/v1/ContentItem",
            "@graph": [
                {
                    "@type": "LtiLinkItem",
                    "mediaType": "application/vnd.ims.lti.v1.ltilink",
                    "url": "http://localhost/lti_launches",
                    "custom": {
                        "deep_linking_uuid": Any.string(),
                        "url": "https://example.com",
                    },
                }
            ],
        }

    @pytest.fixture
    def lti_user(self, application_instance, lti_params):
        return factories.LTIUser(
            application_instance_id=application_instance.id,
            application_instance=application_instance,
            user_id=lti_params["user_id"],
            roles=lti_params["roles"],
        )

    @pytest.fixture
    def authorization_param(self, lti_user):
        return JWTService.encode_with_secret(
            LTIUserService(
                lti_role_service=None, application_instance_service=None
            ).serialize(lti_user),
            secret=TEST_SETTINGS["lms_secret"],
            lifetime=timedelta(days=1),
        )


@pytest.fixture
def lti_params(application_instance, sign_lti_params):
    params = {
        "context_id": "con-182",
        "context_label": "SI182",
        "context_title": "Design of Personal Environments",
        "context_type": "CourseSection",
        "custom_context_memberships_url": "https://apps.imsglobal.org/lti/cert/tp/tp_membership.php/context/con-182/membership?b64=a2puNjk3b3E5YTQ3Z28wZDRnbW5xYzZyYjU%3D",
        "custom_context_setting_url": "https://apps.imsglobal.org/lti/cert/tp/tp_settings.php/lis/CourseSection/con-182/bindings/ims/cert/custom?b64=a2puNjk3b3E5YTQ3Z28wZDRnbW5xYzZyYjU%3D",
        "custom_link_setting_url": "$LtiLink.custom.url",
        "custom_system_setting_url": "https://apps.imsglobal.org/lti/cert/tp/tp_settings.php/ToolProxy/Hypothesis1b40eafba184a131307049e01e9c147d/custom?b64=a2puNjk3b3E5YTQ3Z28wZDRnbW5xYzZyYjU%3D",
        "custom_tc_profile_url": "https://apps.imsglobal.org/lti/cert/tp/tp_tcprofile.php?b64=a2puNjk3b3E5YTQ3Z28wZDRnbW5xYzZyYjU%3D",
        "launch_presentation_document_target": "iframe",
        "launch_presentation_locale": "en_US",
        "launch_presentation_return_url": "https://apps.imsglobal.org/lti/cert/tp/tp_return.php/basic-lti-launch-request",
        "lis_course_section_sourcedid": "id-182",
        "lis_person_contact_email_primary": "jane@school.edu",
        "lis_person_name_family": "Lastname",
        "lis_person_name_full": "Jane Q. Lastname",
        "lis_person_name_given": "Jane",
        "lis_person_sourcedid": "school.edu:jane",
        "lti_message_type": "ContentItemSelectionRequest",
        "lti_version": "LTI-1p0",
        "oauth_callback": "about:blank",
        "oauth_consumer_key": application_instance.consumer_key,
        "oauth_nonce": "38d6db30e395417659d068164ca95169",
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0",
        "roles": "Instructor",
        "tool_consumer_info_product_family_code": "imsglc",
        "tool_consumer_info_version": "1.1",
        "tool_consumer_instance_description": "IMS Testing Description",
        "tool_consumer_instance_guid": application_instance.tool_consumer_instance_guid,
        "tool_consumer_instance_name": "IMS Testing Instance",
        "user_id": "123456",
        "content_item_return_url": "https://apps.imsglobal.org/lti/cert/tp/tp_return.php/basic-lti-launch-request",
    }

    return sign_lti_params(params)


@pytest.fixture
def sign_lti_params(oauth_client):
    def _sign(params):
        params["oauth_signature"] = oauth_client.get_oauth_signature(
            oauthlib.common.Request(
                "http://localhost/content_item_selection", "POST", body=params
            )
        )
        return params

    return _sign
