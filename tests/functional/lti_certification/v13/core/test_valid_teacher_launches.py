import json
import pytest
from lms.resources._js_config import JSConfig


@pytest.mark.filterwarnings("ignore:Using not verified JWT token")
class TestBadPayloads:
    """
    Following the known "bad" payload launches are valid Teacher payloads.

    http://www.imsproject.org/spec/lti/v1p3/cert/#valid-teacher-launches
    """

    def test_message_as_instructor(self, teacher_payload, assert_launch_get_config):
        """Launch LTI 1.3 Message as Instructor"""

        js_config = assert_launch_get_config(teacher_payload)
        assert js_config["mode"] == JSConfig.Mode.CONTENT_ITEM_SELECTION

    def test_with_multiple_roles(self):
        """Launch Instructor with Multiple Role Values"""
        ...

    def test_with_short_role(self):
        """Launch Instructor with Short Role Value"""
        ...

    def test_with_unknown_role(self):
        """Launch Instructor with Unknown Role"""
        ...

    def test_with_no_role(self):
        """Launch Instructor With No Role"""
        ...

    def test_with_only_email(self):
        """Launch Instructor Only Email"""
        ...

    def test_with_only_names(self):
        """Launch Instructor Only Names"""
        ...

    def test_without_pii(self):
        """Launch Instructor No PII"""
        ...

    def test_with_email_no_context(self):
        """Launch Instructor With Email No Context"""
        ...

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
