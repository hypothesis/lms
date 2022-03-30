import pytest


class TestBadPayloads:
    """
    The first few tests will be those that are in one or another way known to be invalid for 1.3 Core Launches.

    http://www.imsproject.org/spec/lti/v1p3/cert/#known-bad-payloads
    """

    def test_no_kid_sent_in_jwt_header(
        self, jwt_headers, make_jwt, student_payload, do_lti_launch
    ):
        """
        The KID is missing from the header of the JWT (preventing the verification of the signing of the JWT)
        """
        del jwt_headers["kid"]

        response = do_lti_launch(
            {"id_token": make_jwt(student_payload, jwt_headers)}, status=403
        )

        assert response.html

    def test_incorrect_kid_in_jwt_header(self):
        """The KID provided is incorrect (and signing verification is impossible)"""
        ...

    def test_wrong_lti_version(self, make_jwt, student_payload, do_lti_launch):
        """The LTI version claim contains the wrong version"""
        student_payload["https://purl.imsglobal.org/spec/lti/claim/version"] = "11.3"

        response = do_lti_launch({"id_token": make_jwt(student_payload)}, status=422)

        assert "There were problems with these request parameters" in response.text
        assert "lti_version" in response.text

    def test_no_lti_version(self, make_jwt, student_payload, do_lti_launch):
        """The LTI version claim is missing"""
        del student_payload["https://purl.imsglobal.org/spec/lti/claim/version"]

        response = do_lti_launch({"id_token": make_jwt(student_payload)}, status=422)

        assert "There were problems with these request parameters" in response.text
        assert "lti_version" in response.text

    def test_invalid_lti_message(self, make_jwt, do_lti_launch):
        """The provided JSON is NOT a 1.3 JWT launch"""
        payload = {"name": "badltilaunch"}

        response = do_lti_launch({"id_token": make_jwt(payload)}, status=403)

        assert response.status_code == 403

    def test_missing_lti_claims(self, student_payload, do_lti_launch, make_jwt):
        """The provided 1.3 JWT launch is missing one or more required claims"""
        missing_claims = [
            "aud",
            "iss",
            "sub",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id",
            "https://purl.imsglobal.org/spec/lti/claim/roles",
        ]
        for missing_claim in missing_claims:
            del student_payload[missing_claim]

        response = do_lti_launch({"id_token": make_jwt(student_payload)}, status=403)

        assert response.status_code == 403
        assert response.html

    @pytest.mark.xfail(reason="JWT verfication disabled")
    def test_timestamps_incorrect(self, student_payload, do_lti_launch, make_jwt):
        """Incorrect JWT iat and exp timestamp Values are Invalid"""
        student_payload["iat"] = 11111
        student_payload["exp"] = 22222

        response = do_lti_launch({"id_token": make_jwt(student_payload)}, status=403)
        assert response.html

    def test_message_type_claim_missing(self, student_payload, assert_missing_claim):
        """The Required message_type Claim Not Present"""
        response = assert_missing_claim(
            student_payload, "https://purl.imsglobal.org/spec/lti/claim/message_type"
        )

        assert "There were problems with these request parameters" in response.text
        assert "message_type" in response.text

    def test_role_claim_missing(self, student_payload, assert_missing_claim):
        """The Required role Claim Not Present"""
        assert_missing_claim(
            student_payload,
            "https://purl.imsglobal.org/spec/lti/claim/roles",
            status=403,
        )

    def test_deployment_id_claim_missing(self, student_payload, assert_missing_claim):
        """The Required deployment_id Claim Not Present"""
        assert_missing_claim(
            student_payload,
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id",
            status=403,
        )

    def test_resource_link_id_claim_missing(
        self, student_payload, assert_missing_claim
    ):
        """The Required resource_link_id Claim Not Present"""
        assert_missing_claim(
            student_payload, "https://purl.imsglobal.org/spec/lti/claim/resource_link"
        )

    def test_user_claim_missing(self, student_payload, assert_missing_claim):
        """The Required sub Claim Not Present"""
        assert_missing_claim(student_payload, "sub", status=403)

    @pytest.fixture
    def assert_missing_claim(self, do_lti_launch, make_jwt):
        def _missing_claim(payload, missing_claim, status=422):
            del payload[missing_claim]

            response = do_lti_launch({"id_token": make_jwt(payload)}, status=status)

            assert response.html

            return response

        return _missing_claim
