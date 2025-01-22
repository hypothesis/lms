import pytest

from tests.functional.lti_certification.v13.assertions import assert_launched_as_student


class TestValidStudentLaunches:
    """
    Test valid instructor payload launches are valid Student/Learner payloads.

    http://www.imsproject.org/spec/lti/v1p3/cert/#valid-student-launches
    """

    def test_message_as_student(self, do_student_launch):
        """Launch LTI 1.3 Message as Student."""

        response = do_student_launch()

        assert_launched_as_student(response)

    def test_with_multiple_roles(self, do_student_launch, student_payload):
        """Launch Student with Multiple Role Values."""
        student_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner",
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Student",
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Mentor",
        ]

        response = do_student_launch()

        assert_launched_as_student(response)

    def test_with_short_role(self, do_student_launch, student_payload):
        """Launch Student with Short Role Value."""
        student_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = ["Learner"]

        response = do_student_launch()

        assert_launched_as_student(response)

    def test_with_unknown_role(self, do_student_launch, student_payload):
        """Launch Student with Unknown Role."""
        student_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner",
            "http://purl.imsglobal.org/vocab/lis/v2/uknownrole/unknown#Unknown",
        ]

        response = do_student_launch()

        assert_launched_as_student(response)

    def test_with_no_role(self, do_student_launch, student_payload):
        """Launch Student With No Role."""
        student_payload["https://purl.imsglobal.org/spec/lti/claim/roles"] = [""]

        response = do_student_launch()

        assert_launched_as_student(response)

    def test_with_only_email(self, do_student_launch, student_payload):
        """Launch Student Only Email."""
        del student_payload["name"]
        del student_payload["given_name"]
        del student_payload["family_name"]
        del student_payload["middle_name"]

        response = do_student_launch()

        assert_launched_as_student(response)

    def test_with_only_names(self, do_student_launch, student_payload):
        """Launch Student Only Names."""
        del student_payload["email"]

        response = do_student_launch()

        assert_launched_as_student(response)

    def test_without_pii(self, do_student_launch, student_payload):
        """Launch Student No PII."""
        del student_payload["name"]
        del student_payload["email"]
        del student_payload["given_name"]
        del student_payload["family_name"]
        del student_payload["middle_name"]

        response = do_student_launch()

        assert_launched_as_student(response)

    @pytest.mark.xfail(
        reason="Pending. Context is required in our schemas", strict=True
    )
    def test_with_email_no_context(self, do_student_launch, student_payload):
        """Launch Student With Email No Context."""

        del student_payload["https://purl.imsglobal.org/spec/lti/claim/context"]

        response = do_student_launch()

        assert_launched_as_student(response)

    @pytest.fixture
    def do_student_launch(self, do_lti_launch, make_jwt, student_payload):
        def do_student_launch():
            return do_lti_launch({"id_token": make_jwt(student_payload)})

        return do_student_launch
