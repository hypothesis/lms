import re
import time

import oauthlib.common
import oauthlib.oauth1
import pytest
from h_matchers import Any
from httpretty import httpretty

from lms.models import ModuleItemConfiguration
from tests import factories


class TestBasicLTILaunch:
    def test_a_good_request_loads_fine(self, app, lti_params):
        response = app.post(
            "/lti_launches",
            params=lti_params,
            headers={
                "Accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            status=200,
        )

        assert response.headers["Content-Type"] == Any.string.matching("^text/html")
        assert response.html

    def test_no_auth_blocks(self, app, lti_params):
        unauthenticated_lti_params = dict(lti_params)
        del unauthenticated_lti_params["oauth_signature"]
        response = app.post(
            "/lti_launches",
            params=unauthenticated_lti_params,
            headers={
                "Accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            status=403,
        )

        assert response.headers["Content-Type"] == Any.string.matching("^text/html")
        assert response.html

    @pytest.fixture(autouse=True)
    def application_instance(self, db_session):  # pylint:disable=unused-argument
        return factories.ApplicationInstance()

    @pytest.fixture(autouse=True, params=["configured", "unconfigured"])
    def module_item_configuration(self, request, db_session):
        if request.param == "unconfigured":
            return

        module_item_configuration = ModuleItemConfiguration(
            resource_link_id="rli-1234",
            tool_consumer_instance_guid="IMS Testing",
            document_url="http://example.com",
        )

        db_session.add(module_item_configuration)
        db_session.commit()

    @pytest.fixture
    def oauth_client(self, application_instance):
        return oauthlib.oauth1.Client(
            application_instance.consumer_key, application_instance.shared_secret
        )

    @pytest.fixture
    def lti_params(self, application_instance, oauth_client):
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
            "tool_consumer_instance_guid": "IMS Testing",
            "tool_consumer_instance_name": "IMS Testing Instance",
            "user_id": "123456",
        }

        params["oauth_signature"] = oauth_client.get_oauth_signature(
            oauthlib.common.Request(
                "http://localhost/lti_launches", "POST", body=params
            )
        )

        return params

    @pytest.fixture(autouse=True)
    def http_intercept(self, _http_intercept):
        """
        Monkey-patch Python's socket core module to mock all HTTP responses.

        We will catch calls to H's API and return 200. All other calls will
        raise an exception, allowing to you see who are are trying to call.
        """
        # We only need to reset once per tests, all other setup can be done
        # once in `_http_intercept()`
        yield
        httpretty.reset()

    @pytest.fixture(scope="session")
    def _http_intercept(self):
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
