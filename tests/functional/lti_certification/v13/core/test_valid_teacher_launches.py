import json

import pytest

from lms.resources._js_config import JSConfig


class TestValidTeacherPayloads:
    """
    Following the known "bad" payload launches are valid Teacher payloads.

    http://www.imsproject.org/spec/lti/v1p3/cert/#valid-teacher-launches
    """

    def test_message_as_instructor(self, teacher_payload, assert_launch_get_config):
        """Launch LTI 1.3 Message as Instructor"""
        js_config = assert_launch_get_config(teacher_payload)
        assert js_config["mode"] == JSConfig.Mode.CONTENT_ITEM_SELECTION

    def test_with_multiple_roles(self, teacher_payload, assert_launch_get_config):
        """Launch Instructor with Multiple Role Values"""
        teacher_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor",
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Staff",
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Other",
        ]

        js_config = assert_launch_get_config(teacher_payload)
        assert js_config["mode"] == JSConfig.Mode.CONTENT_ITEM_SELECTION

    def test_with_short_role(self, teacher_payload, assert_launch_get_config):
        """Launch Instructor with Short Role Value"""
        teacher_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [
            "Instructor"
        ]

        js_config = assert_launch_get_config(teacher_payload)
        assert js_config["mode"] == JSConfig.Mode.CONTENT_ITEM_SELECTION

    def test_with_unknown_role(self, teacher_payload, assert_launch_get_config):
        """Launch Instructor with Unknown Role"""
        teacher_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [
            "http://purl.imsglobal.org/vocab/lis/v2/unknown/unknown#Helper"
        ]

        js_config = assert_launch_get_config(teacher_payload)
        # With non instructor we are not identified as a teacher and not allowed to configure
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH

    def test_with_no_role(self, teacher_payload, assert_launch_get_config):
        """Launch Instructor With No Role"""
        teacher_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [""]

        js_config = assert_launch_get_config(teacher_payload)
        # With non instructor we are not identified as a teacher and not allowed to configure
        assert js_config["mode"] == JSConfig.Mode.BASIC_LTI_LAUNCH

    def test_with_only_email(self, teacher_payload, assert_launch_get_config):
        """Launch Instructor Only Email"""
        del teacher_payload["name"]
        del teacher_payload["given_name"]
        del teacher_payload["family_name"]
        del teacher_payload["middle_name"]

        js_config = assert_launch_get_config(teacher_payload)
        assert js_config["mode"] == JSConfig.Mode.CONTENT_ITEM_SELECTION

    def test_with_only_names(self, teacher_payload, assert_launch_get_config):
        """Launch Instructor Only Names"""
        del teacher_payload["email"]

        js_config = assert_launch_get_config(teacher_payload)
        assert js_config["mode"] == JSConfig.Mode.CONTENT_ITEM_SELECTION

    def test_without_pii(self, teacher_payload, assert_launch_get_config):
        """Launch Instructor No PII"""
        del teacher_payload["name"]
        del teacher_payload["email"]
        del teacher_payload["given_name"]
        del teacher_payload["family_name"]
        del teacher_payload["middle_name"]

        js_config = assert_launch_get_config(teacher_payload)
        assert js_config["mode"] == JSConfig.Mode.CONTENT_ITEM_SELECTION

    @pytest.mark.xfail(reason="Pending. Context is required in our schemas")
    def test_with_email_no_context(self, teacher_payload, assert_launch_get_config):
        """Launch Instructor With Email No Context"""

        del teacher_payload["https://purl.imsglobal.org/spec/lti/claim/context"]

        js_config = assert_launch_get_config(teacher_payload)
        assert js_config["mode"] == JSConfig.Mode.CONTENT_ITEM_SELECTION

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
