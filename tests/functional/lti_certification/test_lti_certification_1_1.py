import time
from urllib.parse import parse_qs, urlparse

import oauthlib.common
import oauthlib.oauth1
import pytest
from h_matchers import Any

from lms.models import ApplicationInstance
from tests.functional.base_class import TestBaseClass


class TestLTICertification(TestBaseClass):
    SHARED_SECRET = "TEST_SECRET"
    OAUTH_CONSUMER_KEY = "Hypothesis1b40eafba184a131307049e01e9c147d"
    OAUTH_NONCE = "38d6db30e395417659d068164ca95169"
    OAUTH_CLIENT = oauthlib.oauth1.Client(OAUTH_CONSUMER_KEY, SHARED_SECRET)

    def test_a_good_request_loads_fine(self, app, lti_params):
        result = self.lti_launch(app, lti_params, status=200)

        self.assert_response_is_html(result)

        # Check a random parameter to see it's passed to the body
        assert "tool_consumer_instance_guid" in result.text
        assert lti_params["tool_consumer_instance_guid"] in result.text

    def test_1_1_redirect_to_tool_consumer_when_resource_link_id_missing(
        self, app, lti_params
    ):
        """
        No resource_link_id provided.

        Expected result: Return user to the Tool Consumer with an error message.
        """
        lti_params.pop("resource_link_id")

        self.assert_redirected_to_tool_with_message(
            app, lti_params, message=Any.string.containing("resource_link_id")
        )

    def test_1_2_nice_message_when_res_link_id_and_return_url_missing(
        self, app, lti_params
    ):
        """
        No resource_link_id or return URL provided.

        Expected result: A user-friendly error message.
        """
        lti_params.pop("resource_link_id")
        lti_params.pop("launch_presentation_return_url")

        result = self.lti_launch(app, lti_params, status=422)

        self.assert_response_is_html(result)
        assert "resource_link_id" in result

    def test_1_5_redirect_to_tool_consumer_when_lti_version_invalid(
        self, app, lti_params
    ):
        """
        Invalid LTI version.

        Return user to the Tool Consumer with an error message.
        """
        lti_params["lti_version"] = "LTI-1"

        self.assert_redirected_to_tool_with_message(
            app, lti_params, message=Any.string.containing("lti_version")
        )

    def test_1_6_redirect_to_tool_consumer_when_lti_version_wrong(
        self, app, lti_params
    ):
        """
        Wrong LTI version.

        Expected result: Return user to the Tool Consumer with an error message.
                """
        lti_params["lti_version"] = "LTI-2p0"

        self.assert_redirected_to_tool_with_message(
            app, lti_params, message=Any.string.containing("lti_version")
        )

    def test_1_7_redirect_to_tool_consumer_when_lti_version_missing(
        self, app, lti_params
    ):
        """
        Missing LTI version.

        Expected result: Return user to the Tool Consumer with an error message.
        """
        lti_params.pop("lti_version")

        self.assert_redirected_to_tool_with_message(
            app, lti_params, message=Any.string.containing("lti_version")
        )

    def test_1_8_redirect_to_tool_consumer_when_lti_mesage_type_invalid(
        self, app, lti_params
    ):
        """
        Invalid LTI message type.

        Expected result: Return user to the Tool Consumer with an error message.
        """
        lti_params["lti_message_type"] = "a-basic-lti-launch-request"

        self.assert_redirected_to_tool_with_message(
            app, lti_params, message=Any.string.containing("lti_message_type")
        )

    def test_1_9_redirect_to_tool_consumer_when_lti_message_type_missing(
        self, app, lti_params
    ):
        """
        Missing LTI message type

        Expected result: Return user to the Tool Consumer with an error message.
        """
        lti_params.pop("lti_message_type")

        self.assert_redirected_to_tool_with_message(
            app, lti_params, message=Any.string.containing("lti_message_type")
        )

    def test_4_5_placeholder(self, app, lti_params):
        """
        Launch as an instructor with no context or personal information apart
        from the context ID.

        Expected result: User should have privileges appropriate to an
        instructor (e.g. able to edit) unless context and/or personal information
        is required in which case access should be denied and the user returned
        to the Tool Consumer with a user-friendly message
        """
        lti_params = self.update_params(
            lti_params,
            remove={
                "resource_link_title",
                "context_label",
                "lis_person_contact_email_primary",
                "lis_course_section_sourcedid",
                "context_type",
                "lis_person_name_given",
                "context_title",
                "resourcelinkid",
                "lis_person_name_full",
                "lis_person_name_family",
            },
            add={
                "custom_context_memberships_url": "https://apps.imsglobal.org/lti/cert/tp/tp_membership.php/context/con-182/membership?b64=a3BwZGwzZGhvdGRsdHBkcDV2dWh1aDQzYzE%3D",
                "custom_context_setting_url": "https://apps.imsglobal.org/lti/cert/tp/tp_settings.php/lis/CourseSection/con-182/bindings/ims/cert/custom?b64=a3BwZGwzZGhvdGRsdHBkcDV2dWh1aDQzYzE%3D",
                "custom_link_setting_url": "https://apps.imsglobal.org/lti/cert/tp/tp_settings.php/links/rli-1234/custom?b64=a3BwZGwzZGhvdGRsdHBkcDV2dWh1aDQzYzE%3D",
                "custom_system_setting_url": "https://apps.imsglobal.org/lti/cert/tp/tp_settings.php/ToolProxy/Hypothesis4dd96539c449ca5c3d57cc3d778d6bf3/custom?b64=a3BwZGwzZGhvdGRsdHBkcDV2dWh1aDQzYzE%3D",
                "custom_tc_profile_url": "https://apps.imsglobal.org/lti/cert/tp/tp_tcprofile.php?b64=a3BwZGwzZGhvdGRsdHBkcDV2dWh1aDQzYzE%3D",
            },
        )

        self.assert_redirected_to_tool_with_message(
            app, lti_params, message=Any.string.containing("_placeholder")
        )

    def test_4_6_placeholder(self, app, lti_params):
        """
        Launch as Instructor with no context information.

        Expected result: User should have privileges appropriate to an
        instructor (e.g. able to edit) unless context and/or personal
        information is required in which case access should be denied and
        the user returned to the Tool Consumer with a user-friendly message.
        """

        lti_params = self.update_params(
            lti_params,
            remove={
                "resource_link_title",
                "context_label",
                "lis_course_section_sourcedid",
                "custom_link_setting_url",
                "context_type",
                "context_title",
                "custom_context_setting_url",
                "resourcelinkid",
                "context_id",
            },
            add={
                "custom_context_memberships_url": "$ToolProxyBinding.memberships.url",
                "custom_system_setting_url": "https://apps.imsglobal.org/lti/cert/tp/tp_settings.php/ToolProxy/Hypothesis4dd96539c449ca5c3d57cc3d778d6bf3/custom?b64=a3BwZGwzZGhvdGRsdHBkcDV2dWh1aDQzYzE%3D",
                "custom_tc_profile_url": "https://apps.imsglobal.org/lti/cert/tp/tp_tcprofile.php?b64=a3BwZGwzZGhvdGRsdHBkcDV2dWh1aDQzYzE%3D",
            },
        )

        self.assert_redirected_to_tool_with_message(
            app, lti_params, message=Any.string.containing("_placeholder")
        )

    # ---------------------------------------------------------------------- #
    # Assertions

    @classmethod
    def assert_response_is_html(cls, response):
        assert response.headers["Content-Type"] == Any.string.matching("^text/html")
        assert response.html

    @classmethod
    def assert_redirected_to_tool_with_message(
        cls, app, lti_params, message=Any.string()
    ):
        response = cls.lti_launch(app, lti_params, status=302)

        expected_url = lti_params["launch_presentation_return_url"]
        url = urlparse(response.headers["Location"])

        assert url._replace(query=None).geturl() == expected_url
        assert parse_qs(url.query) == Any.dict.containing({"lti_msg": [message]})

    # ---------------------------------------------------------------------- #
    # Helper methods

    @classmethod
    def update_params(cls, params, remove=None, add=None):
        if remove:
            for item in remove:
                params.pop(item)

        if add:
            params.update(add)

        return params

    @classmethod
    def lti_launch(cls, app, params, status=200):
        url = "/lti_launches"

        params = cls.oauth_sign_params(url, params)

        return app.post(
            url,
            params=params,
            headers={
                "Accept": "text/html",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            status=status,
        )

    @classmethod
    def oauth_sign_params(cls, url, params):
        params.update(
            {
                "oauth_consumer_key": cls.OAUTH_CONSUMER_KEY,
                "oauth_nonce": cls.OAUTH_NONCE,
                "oauth_timestamp": str(int(time.time())),
            }
        )
        params["oauth_signature"] = cls.OAUTH_CLIENT.get_oauth_signature(
            oauthlib.common.Request(f"http://localhost{url}", "POST", body=params)
        )

        return params

    # Fixtures ------------------------------------------------------------- #

    @pytest.fixture(autouse=True)
    def application_instance(self, db_session, app):
        # Load app so we create the instance after the DB has been truncated

        application_instance = ApplicationInstance(
            consumer_key=self.OAUTH_CONSUMER_KEY,
            shared_secret=self.SHARED_SECRET,
            lms_url="test_lms_url",
            requesters_email="test_requesters_email",
        )

        db_session.add(application_instance)
        db_session.commit()

        return application_instance

    @pytest.fixture
    def lti_params(self):
        return self.json_fixture("lti_certification/all_params_v1.1.json")
