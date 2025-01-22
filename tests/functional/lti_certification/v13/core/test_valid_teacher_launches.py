import pytest

from tests.functional.lti_certification.v13.assertions import (
    assert_launched_as_student,
    assert_launched_as_teacher,
)


class TestValidTeacherPayloads:
    """
    Following the known "bad" payload launches are valid Teacher payloads.

    http://www.imsproject.org/spec/lti/v1p3/cert/#valid-teacher-launches
    """

    def test_message_as_instructor(self, do_teacher_launch):
        """Launch LTI 1.3 Message as Instructor."""
        response = do_teacher_launch()

        assert_launched_as_teacher(response)

    def test_with_multiple_roles(self, do_teacher_launch, teacher_payload):
        """Launch Instructor with Multiple Role Values."""
        teacher_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor",
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Staff",
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Other",
        ]

        response = do_teacher_launch()

        assert_launched_as_teacher(response)

    def test_with_short_role(self, do_teacher_launch, teacher_payload):
        """Launch Instructor with Short Role Value."""
        teacher_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [
            "Instructor"
        ]

        response = do_teacher_launch()

        assert_launched_as_teacher(response)

    def test_with_unknown_role(self, do_teacher_launch, teacher_payload):
        """Launch Instructor with Unknown Role."""
        teacher_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [
            "http://purl.imsglobal.org/vocab/lis/v2/unknown/unknown#Helper"
        ]

        response = do_teacher_launch()

        # With non instructor roles we are not identified as a teacher and not
        # allowed to configure
        assert_launched_as_student(response)

    def test_with_no_role(self, do_teacher_launch, teacher_payload):
        """Launch Instructor With No Role."""
        teacher_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [""]

        response = do_teacher_launch()

        # With non instructor roles we are not identified as a teacher and not
        # allowed to configure
        assert_launched_as_student(response)

    def test_with_only_email(self, do_teacher_launch, teacher_payload):
        """Launch Instructor Only Email."""
        del teacher_payload["name"]
        del teacher_payload["given_name"]
        del teacher_payload["family_name"]
        del teacher_payload["middle_name"]

        response = do_teacher_launch()

        assert_launched_as_teacher(response)

    def test_with_only_names(self, do_teacher_launch, teacher_payload):
        """Launch Instructor Only Names."""
        del teacher_payload["email"]

        response = do_teacher_launch()

        assert_launched_as_teacher(response)

    def test_without_pii(self, do_teacher_launch, teacher_payload):
        """Launch Instructor No PII."""
        del teacher_payload["name"]
        del teacher_payload["email"]
        del teacher_payload["given_name"]
        del teacher_payload["family_name"]
        del teacher_payload["middle_name"]

        response = do_teacher_launch()

        assert_launched_as_teacher(response)

    @pytest.mark.xfail(reason="Pending. Context is required in our schemas")
    def test_with_email_no_context(self, do_teacher_launch, teacher_payload):
        """Launch Instructor With Email No Context."""

        del teacher_payload["https://purl.imsglobal.org/spec/lti/claim/context"]

        response = do_teacher_launch()

        assert_launched_as_teacher(response)

    @pytest.fixture
    def do_teacher_launch(self, do_lti_launch, make_jwt, teacher_payload):
        def do_teacher_launch():
            return do_lti_launch({"id_token": make_jwt(teacher_payload)})

        return do_teacher_launch
