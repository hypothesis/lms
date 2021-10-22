import re
import time
from urllib.parse import urlencode

import oauthlib.common
import oauthlib.oauth1
import pytest
from h_matchers import Any
from httpretty import httpretty

from lms.models import Assignment
from lms.resources._js_config import JSConfig
from tests import factories


class TestBasicLTILaunch:
    def test_requests_with_no_oauth_signature_are_forbidden(self, app, lti_params):
        del lti_params["oauth_signature"]

        response = app.post(
            "/lti_launches",
            params=lti_params,
            headers={
                "Accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            status=403,
        )

        assert response.headers["Content-Type"] == Any.string.matching("^text/html")
        assert response.html

    def test_unconfigured_basic_lti_launch(self, app, lti_params):
        response = app.post(
            "/lti_launches",
            params=lti_params,
            headers={
                "Accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            status=200,
        )

        assert f'"mode": "{JSConfig.Mode.CONTENT_ITEM_SELECTION}"' in response.text

    def test_db_configured_basic_lti_launch(self, app, lti_params, assignment):
        response = app.post(
            "/lti_launches",
            params=lti_params,
            headers={
                "Accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            status=200,
        )

        assert f'"mode": "{JSConfig.Mode.BASIC_LTI_LAUNCH}"' in response.text
        assert urlencode({"url": assignment.document_url}) in response.text

    def test_url_configured_basic_lti_launch(self, app, lti_params, sign_lti_params):
        document_url = "https://url-configured.com/document.pdf"
        response = app.post(
            "/lti_launches",
            params=sign_lti_params(dict(lti_params, url=document_url)),
            headers={
                "Accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            status=200,
        )

        assert f'"mode": "{JSConfig.Mode.BASIC_LTI_LAUNCH}"' in response.text
        assert urlencode({"url": document_url}) in response.text

    @pytest.mark.usefixtures("legacy_speed_grader_assignment")
    def test_url_configured_basic_lti_launch_legacy_speed_grader_launch(
        self,
        app,
        legacy_speed_grader_lti_params,
        sign_lti_params,
    ):
        document_url = "https://url-configured.com/document.pdf"
        response = app.post(
            "/lti_launches?learner_canvas_user_id=USER_ID",
            params=sign_lti_params(
                dict(legacy_speed_grader_lti_params, url=document_url)
            ),
            headers={
                "Accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            status=200,
        )

        assert f'"mode": "{JSConfig.Mode.BASIC_LTI_LAUNCH}"' in response.text
        assert urlencode({"url": document_url}) in response.text

    def test_legacy_canvas_file_basic_lti_launch(
        self, app, lti_params, sign_lti_params, db_session
    ):
        canvas_file_id = "1"
        canvas_course_id = "2"
        response = app.post(
            "/lti_launches",
            params=sign_lti_params(
                dict(
                    lti_params,
                    canvas_file="true",
                    custom_canvas_course_id=canvas_course_id,
                    file_id=canvas_file_id,
                    ext_lti_assignment_id="EXT_LTI_ASSIGMENT_ID",
                )
            ),
            headers={
                "Accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            status=200,
        )

        assert f'"mode": "{JSConfig.Mode.BASIC_LTI_LAUNCH}"' in response.text
        assert (
            db_session.query(Assignment)
            .filter_by(
                document_url=f"canvas://file/course/{canvas_course_id}/file_id/{canvas_file_id}"
            )
            .count()
            == 1
        )

    @pytest.mark.usefixtures("legacy_speed_grader_assignment")
    def test_legacy_canvas_file_legacy_speed_grader_launch(
        self,
        app,
        legacy_speed_grader_lti_params,
        sign_lti_params,
        db_session,
    ):
        canvas_file_id = "1"
        canvas_course_id = "2"
        response = app.post(
            "/lti_launches?learner_canvas_user_id=USER_ID",
            params=sign_lti_params(
                dict(
                    legacy_speed_grader_lti_params,
                    canvas_file="true",
                    custom_canvas_course_id=canvas_course_id,
                    file_id=canvas_file_id,
                )
            ),
            headers={
                "Accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            status=200,
        )

        assert f'"mode": "{JSConfig.Mode.BASIC_LTI_LAUNCH}"' in response.text
        assert (
            db_session.query(Assignment)
            .filter_by(
                document_url=f"canvas://file/course/{canvas_course_id}/file_id/{canvas_file_id}"
            )
            .count()
            == 1
        )

    @pytest.fixture(autouse=True)
    def application_instance(self, db_session):  # pylint:disable=unused-argument
        return factories.ApplicationInstance(tool_consumer_instance_guid="IMS Testing")

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
    def legacy_speed_grader_assignment(
        self, db_session, application_instance, legacy_speed_grader_lti_params
    ):
        assignment = Assignment(
            resource_link_id=legacy_speed_grader_lti_params["resource_link_id"],
            tool_consumer_instance_guid=application_instance.tool_consumer_instance_guid,
            document_url="http://legacy-speed-grader.com/document.pdf",
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
    def legacy_speed_grader_lti_params(self, lti_params, sign_lti_params):
        # Legacy speed grader launches will send the wrong resource_link_id
        # on the POST params and not include the right one on the query params.
        lti_params["resource_link_id"] = lti_params["context_id"]
        return sign_lti_params(lti_params)

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

    @pytest.fixture(autouse=True)
    def http_intercept(self):
        """
        Monkey-patch Python's socket core module to mock all HTTP responses.

        We will catch calls to H's API and return 200. All other calls will
        raise an exception, allowing to you see who are are trying to call.
        """
        # Mock all calls to the H API
        httpretty.register_uri(
            method=Any(),
            uri=re.compile(r"^https://example.com/private/api/.*"),
            body="",
        )

        # Catch URLs we aren't expecting or have failed to mock
        def error_response(request, uri, _response_headers):
            raise NotImplementedError(f"Unexpected call to URL: {request.method} {uri}")

        httpretty.register_uri(method=Any(), uri=re.compile(".*"), body=error_response)

        httpretty.enable()
        yield
        httpretty.disable()
