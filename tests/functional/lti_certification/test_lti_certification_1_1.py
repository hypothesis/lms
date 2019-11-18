import time
from urllib.parse import parse_qs, urlparse

import oauthlib.common
import oauthlib.oauth1
import pytest
from h_matchers import Any

from lms.models import ApplicationInstance, ModuleItemConfiguration
from tests.functional.base_class import TestBaseClass


class TestLTICertification(TestBaseClass):
    SHARED_SECRET = "TEST_SECRET"
    OAUTH_CONSUMER_KEY = "Hypothesis1b40eafba184a131307049e01e9c147d"
    OAUTH_NONCE = "38d6db30e395417659d068164ca95169"
    OAUTH_CLIENT = oauthlib.oauth1.Client(OAUTH_CONSUMER_KEY, SHARED_SECRET)

    def test_a_good_request_loads_fine(self, app, lti_params_1x):
        result = self.lti_launch(app, lti_params_1x, status=200)

        self.assert_response_is_html(result)

    def test_1_1_redirect_to_tool_consumer_when_resource_link_id_missing(
        self, app, lti_params_1x
    ):
        """
        No resource_link_id provided.

        Expected result: Return user to the Tool Consumer with an error message.
        """
        lti_params_1x.pop("resource_link_id")

        self.assert_redirected_to_tool_with_message(
            app, lti_params_1x, message=Any.string.containing("resource_link_id")
        )

    def test_1_2_nice_message_when_res_link_id_and_return_url_missing(
        self, app, lti_params_1x
    ):
        """
        No resource_link_id or return URL provided.

        Expected result: A user-friendly error message.
        """
        lti_params_1x.pop("resource_link_id")
        lti_params_1x.pop("launch_presentation_return_url")

        result = self.lti_launch(app, lti_params_1x, status=422)

        self.assert_response_is_html(result)
        assert "resource_link_id" in result

    def test_1_5_redirect_to_tool_consumer_when_lti_version_invalid(
        self, app, lti_params_1x
    ):
        """
        Invalid LTI version.

        Return user to the Tool Consumer with an error message.
        """
        lti_params_1x["lti_version"] = "LTI-1"

        self.assert_redirected_to_tool_with_message(
            app, lti_params_1x, message=Any.string.containing("lti_version")
        )

    def test_1_6_redirect_to_tool_consumer_when_lti_version_wrong(
        self, app, lti_params_1x
    ):
        """
        Wrong LTI version.

        Expected result: Return user to the Tool Consumer with an error message.
                """
        lti_params_1x["lti_version"] = "LTI-2p0"

        self.assert_redirected_to_tool_with_message(
            app, lti_params_1x, message=Any.string.containing("lti_version")
        )

    def test_1_7_redirect_to_tool_consumer_when_lti_version_missing(
        self, app, lti_params_1x
    ):
        """
        Missing LTI version.

        Expected result: Return user to the Tool Consumer with an error message.
        """
        lti_params_1x.pop("lti_version")

        self.assert_redirected_to_tool_with_message(
            app, lti_params_1x, message=Any.string.containing("lti_version")
        )

    def test_1_8_redirect_to_tool_consumer_when_lti_mesage_type_invalid(
        self, app, lti_params_1x
    ):
        """
        Invalid LTI message type.

        Expected result: Return user to the Tool Consumer with an error message.
        """
        lti_params_1x["lti_message_type"] = "a-basic-lti-launch-request"

        self.assert_redirected_to_tool_with_message(
            app, lti_params_1x, message=Any.string.containing("lti_message_type")
        )

    def test_1_9_redirect_to_tool_consumer_when_lti_message_type_missing(
        self, app, lti_params_1x
    ):
        """
        Missing LTI message type

        Expected result: Return user to the Tool Consumer with an error message.
        """
        lti_params_1x.pop("lti_message_type")

        self.assert_redirected_to_tool_with_message(
            app, lti_params_1x, message=Any.string.containing("lti_message_type")
        )

    def test_4_5_redirect_to_tool_for_instructor_with_no_context_bar_id(
        self, app, lti_params_4x
    ):
        """
        Launch as an instructor with no context or personal information apart
        from the context ID.

        Expected result: User should have privileges appropriate to an
        instructor (e.g. able to edit) unless context and/or personal information
        is required in which case access should be denied and the user returned
        to the Tool Consumer with a user-friendly message

        Hypotheis note: context_title is required for us
        See: See: https://github.com/hypothesis/lms/wiki/LTI-Parameters-Required-for-Hypothesis-LMS-App-Integration
        """
        lti_params_4x = self.update_params(
            lti_params_4x,
            remove=[
                "context_label",
                "context_title",
                "context_type",
                "lis_course_section_sourcedid",
                "lis_person_contact_email_primary",
                "lis_person_name_family",
                "lis_person_name_full",
                "lis_person_name_given",
                "resource_link_title",
            ],
        )

        self.assert_redirected_to_tool_with_message(
            app, lti_params_4x, message=Any.string.matching(".*")
        )

    def test_4_6_redirect_to_tool_for_instructor_with_no_context(
        self, app, lti_params_4x
    ):
        """
        Launch as Instructor with no context information.

        Expected result: User should have privileges appropriate to an
        instructor (e.g. able to edit) unless context and/or personal
        information is required in which case access should be denied and
        the user returned to the Tool Consumer with a user-friendly message.

        Hypotheis note: context_id and context_title are required for us:
        See: https://github.com/hypothesis/lms/wiki/LTI-Parameters-Required-for-Hypothesis-LMS-App-Integration
        """

        lti_params_4x = self.update_params(
            lti_params_4x,
            remove=[
                "context_id",
                "context_label",
                "context_title",
                "context_type",
                "custom_context_setting_url",
                "custom_link_setting_url",
                "lis_course_section_sourcedid",
                "resource_link_title",
            ],
            # I've no idea why this is different, but it's in the spec tests
            add={"custom_context_memberships_url": "$ToolProxyBinding.memberships.url"},
        )

        self.assert_redirected_to_tool_with_message(
            app, lti_params_4x, message=Any.string.matching(".*")
        )

    # ---------------------------------------------------------------------- #
    # Assertions

    @classmethod
    def assert_response_is_html(cls, response):
        assert response.headers["Content-Type"] == Any.string.matching("^text/html")
        assert response.html

    @classmethod
    def assert_redirected_to_tool_with_message(
        cls, app, lti_params_1x, message=Any.string()
    ):
        response = cls.lti_launch(app, lti_params_1x, status=302)

        expected_url = lti_params_1x["launch_presentation_return_url"]
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

    @pytest.fixture(autouse=True, params=["configured", "unconfigured"])
    def module_item_configuration(self, request, db_session, application_instance):
        if request.param == "unconfigured":
            return

        module_item_configuration = ModuleItemConfiguration(
            resource_link_id="rli-1234",
            tool_consumer_instance_guid="IMS Testing",
            document_url="http://example.com",
        )

        db_session.add(module_item_configuration)
        db_session.commit()

        return module_item_configuration

    @pytest.fixture
    def lti_params_1x(self):
        """LTI launch params for testing section 1.x tests."""
        return self.json_fixture("lti_certification/v1.1/section_1.json")

    @pytest.fixture
    def lti_params_4x(self):
        """LTI launch params for testing section 4.x tests."""
        return self.json_fixture("lti_certification/v1.1/section_4.json")
