import json

import pytest

from lms.resources._js_config import JSConfig


@pytest.mark.xfail(cause="Work in progress")
class TestValidStudentLaunches:
    """
    Following the various valid instructor payload launches are valid Student/Learner payloads

    http://www.imsproject.org/spec/lti/v1p3/cert/#valid-student-launches
    """

    def test_message_as_student(self, student_payload, assert_launch_get_config):
        """Launch LTI 1.3 Message as Student"""
        js_config = assert_launch_get_config(student_payload)
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH

    def test_with_multiple_roles(self, student_payload, assert_launch_get_config):
        """Launch Student with Multiple Role Values"""
        student_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner",
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Student",
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Mentor",
        ]

        js_config = assert_launch_get_config(student_payload)
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH

    def test_with_short_role(self, student_payload, assert_launch_get_config):
        """Launch Student with Short Role Value"""
        student_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = ["Learner"]

        js_config = assert_launch_get_config(student_payload)
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH

    def test_with_unknown_role(self, student_payload, assert_launch_get_config):
        """Launch Student with Unknown Role"""
        student_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner",
            "http://purl.imsglobal.org/vocab/lis/v2/uknownrole/unknown#Unknown",
        ]

        js_config = assert_launch_get_config(student_payload)
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH

    def test_with_no_role(self, student_payload, assert_launch_get_config):
        """Launch Student With No Role"""
        student_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [""]

        js_config = assert_launch_get_config(student_payload)
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH

    def test_with_only_email(self, student_payload, assert_launch_get_config):
        """Launch Student Only Email"""
        del student_payload["name"]
        del student_payload["given_name"]
        del student_payload["family_name"]
        del student_payload["middle_name"]

        js_config = assert_launch_get_config(student_payload)
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH

    def test_with_only_names(self, student_payload, assert_launch_get_config):
        """Launch Student Only Names"""
        del student_payload["email"]

        js_config = assert_launch_get_config(student_payload)
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH

    def test_without_pii(self, student_payload, assert_launch_get_config):
        """Launch Student No PII"""
        del student_payload["name"]
        del student_payload["email"]
        del student_payload["given_name"]
        del student_payload["family_name"]
        del student_payload["middle_name"]

        js_config = assert_launch_get_config(student_payload)
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH

    @pytest.mark.xfail(reason="Pending. Context is required in our schemas")
    def test_with_email_no_context(self, student_payload, assert_launch_get_config):
        """Launch Student With Email No Context"""

        del student_payload["https://purl.imsglobal.org/spec/lti/claim/context"]

        js_config = assert_launch_get_config(student_payload)
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH

    @pytest.fixture
    def assert_launch_get_config(self, do_lti_launch, make_jwt):
        def _assert_launch(payload):
            response = do_lti_launch({"id_token": make_jwt(payload)}, status=200)

            assert response.status_code == 200
            assert response.html
            return json.loads(
                response.html.find("script", {"class": "js-config"}).string
            )

        return _assert_launch
