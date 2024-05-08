import json
import time
from urllib.parse import urlencode

import oauthlib.common
import oauthlib.oauth1
import pytest
from h_matchers import Any

from lms.models import Assignment
from lms.resources._js_config import JSConfig
from tests import factories


class TestBasicLTILaunch:
    def test_requests_with_no_oauth_signature_are_forbidden(
        self, lti_params, do_lti_launch
    ):
        del lti_params["oauth_signature"]

        response = do_lti_launch(post_params=lti_params, status=403)

        assert response.headers["Content-Type"] == Any.string.matching("^text/html")
        assert response.html

    def test_unconfigured_basic_lti_launch(self, lti_params, do_lti_launch):
        response = do_lti_launch(
            post_params=lti_params,
            status=200,
        )

        assert self.get_client_config(response)["mode"] == JSConfig.Mode.FILE_PICKER

    def test_db_configured_basic_lti_launch(
        self, lti_params, assignment, do_lti_launch
    ):
        response = do_lti_launch(post_params=lti_params, status=200)

        js_config = self.get_client_config(response)
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH
        assert urlencode({"url": assignment.document_url}) in js_config["viaUrl"]

    def test_basic_lti_launch_canvas_deep_linking_url(
        self, do_lti_launch, url_launch_params, db_session
    ):
        get_params, post_params = url_launch_params

        response = do_lti_launch(
            get_params=get_params, post_params=post_params, status=200
        )

        js_config = self.get_client_config(response)
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH
        assert (
            urlencode({"url": "https://url-configured.com/document.pdf"})
            in js_config["viaUrl"]
        )
        assert (
            db_session.query(Assignment)
            .filter_by(document_url="https://url-configured.com/document.pdf")
            .count()
            == 1
        )

    def test_basic_lti_launch_canvas_deep_linking_canvas_file(
        self, do_lti_launch, db_session, canvas_file_launch_params
    ):
        get_params, post_params = canvas_file_launch_params

        response = do_lti_launch(
            get_params=get_params, post_params=post_params, status=200
        )

        js_config = self.get_client_config(response)
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH
        assert (
            js_config["api"]["viaUrl"]["path"]
            == "/api/canvas/assignments/rli-1234/via_url"
        )
        assert (
            db_session.query(Assignment)
            .filter_by(document_url="canvas://file/course/1/file_id/2")
            .count()
            == 1
        )

    @pytest.fixture(autouse=True)
    def application_instance(self, db_session):  # noqa: ARG002
        return factories.ApplicationInstance(
            tool_consumer_instance_guid="IMS Testing",
            organization=factories.Organization(),
        )

    @pytest.fixture
    def assignment(self, db_session, application_instance, lti_params):
        assignment = Assignment(
            resource_link_id=lti_params["resource_link_id"],
            tool_consumer_instance_guid=application_instance.tool_consumer_instance_guid,
            document_url="http://db-configured.com/document.pdf",
        )

        db_session.add(assignment)
        db_session.commit()

        return assignment

    @pytest.fixture
    def oauth_client(self, application_instance):
        return oauthlib.oauth1.Client(
            application_instance.consumer_key, application_instance.shared_secret
        )

    @pytest.fixture
    def lti_params(self, application_instance, sign_lti_params):
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
            "lti_message_type": "basic-lti-launch-request",
            "lti_version": "LTI-1p0",
            "oauth_callback": "about:blank",
            "oauth_consumer_key": application_instance.consumer_key,
            "oauth_nonce": "38d6db30e395417659d068164ca95169",
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_version": "1.0",
            "resource_link_id": "rli-1234",
            "resource_link_title": "Link 1234",
            "resourcelinkid": "rli-1234",
            "roles": "Instructor",
            "tool_consumer_info_product_family_code": "imsglc",
            "tool_consumer_info_version": "1.1",
            "tool_consumer_instance_description": "IMS Testing Description",
            "tool_consumer_instance_guid": application_instance.tool_consumer_instance_guid,
            "tool_consumer_instance_name": "IMS Testing Instance",
            "user_id": "123456",
        }

        return sign_lti_params(params)

    @pytest.fixture
    def canvas_file_launch_params(self, lti_params, sign_lti_params):
        return {"canvas_file": "true", "file_id": "2"}, sign_lti_params(
            dict(
                lti_params,
                custom_canvas_course_id="1",
                tool_consumer_info_product_family_code="canvas",
            )
        )

    @pytest.fixture
    def url_launch_params(self, lti_params, sign_lti_params):
        return {}, sign_lti_params(
            dict(
                lti_params,
                url="https://url-configured.com/document.pdf",
                tool_consumer_info_product_family_code="canvas",
            )
        )

    @pytest.fixture
    def sign_lti_params(self, oauth_client):
        def _sign(params):
            params["oauth_signature"] = oauth_client.get_oauth_signature(
                oauthlib.common.Request(
                    "http://localhost/lti_launches", "POST", body=params
                )
            )
            return params

        return _sign

    def get_client_config(self, response):
        return json.loads(response.html.find("script", {"class": "js-config"}).string)
