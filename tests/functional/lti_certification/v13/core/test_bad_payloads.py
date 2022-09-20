import logging

import pytest
from h_matchers import Any


class TestBadPayloads:
    """
    The first few tests will be those that are in one or another way known to be invalid for 1.3 Core Launches.

    http://www.imsproject.org/spec/lti/v1p3/cert/#known-bad-payloads
    """

    def test_no_kid_sent_in_jwt_header(
        self, jwt_headers, make_jwt, test_payload, do_lti_launch, caplog
    ):
        """
        The KID is missing from the header of the JWT (preventing the verification of the signing of the JWT)
        """
        del jwt_headers["kid"]

        do_lti_launch({"id_token": make_jwt(test_payload, jwt_headers)}, status=422)

        assert "Missing 'kid' value in JWT header" in caplog.messages

    def test_incorrect_kid_in_jwt_header(
        self, jwt_headers, test_payload, do_lti_launch, make_jwt, caplog
    ):
        jwt_headers["kid"] = "imstester_66067"

        do_lti_launch({"id_token": make_jwt(test_payload, jwt_headers)}, status=422)
        assert (
            Any.string.matching(
                "^Invalid JWT for:.* Unable to find a signing key that matches:.*$"
            )
            in caplog.messages
        )

    def test_wrong_lti_version(self, make_jwt, test_payload, do_lti_launch):
        """The LTI version claim contains the wrong version"""
        test_payload["https://purl.imsglobal.org/spec/lti/claim/version"] = "11.3"

        response = do_lti_launch({"id_token": make_jwt(test_payload)}, status=422)

        assert "There were problems with these request parameters" in response.text
        assert "lti_version" in response.text

    def test_no_lti_version(self, make_jwt, test_payload, do_lti_launch):
        """The LTI version claim is missing"""
        del test_payload["https://purl.imsglobal.org/spec/lti/claim/version"]

        response = do_lti_launch({"id_token": make_jwt(test_payload)}, status=422)

        assert "There were problems with these request parameters" in response.text
        assert "lti_version" in response.text

    def test_invalid_lti_message(self, make_jwt, do_lti_launch):
        """The provided JSON is NOT a 1.3 JWT launch"""
        payload = {"name": "badltilaunch"}

        response = do_lti_launch({"id_token": make_jwt(payload)}, status=422)

        assert response.status_code == 422

    def test_missing_lti_claims(self, test_payload, do_lti_launch, make_jwt):
        """The provided 1.3 JWT launch is missing one or more required claims"""
        missing_claims = [
            "aud",
            "iss",
            "sub",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id",
            "https://purl.imsglobal.org/spec/lti/claim/roles",
        ]
        for missing_claim in missing_claims:
            del test_payload[missing_claim]

        response = do_lti_launch({"id_token": make_jwt(test_payload)}, status=422)

        assert response.status_code == 422
        assert response.html

    def test_timestamps_incorrect(self, test_payload, do_lti_launch, make_jwt):
        """Incorrect JWT iat and exp timestamp Values are Invalid"""
        test_payload["iat"] = 11111
        test_payload["exp"] = 22222

        response = do_lti_launch({"id_token": make_jwt(test_payload)}, status=422)
        assert response.html

    def test_message_type_claim_missing(self, test_payload, assert_missing_claim):
        """The Required message_type Claim Not Present"""
        response = assert_missing_claim(
            test_payload, "https://purl.imsglobal.org/spec/lti/claim/message_type"
        )

        assert "There were problems with these request parameters" in response.text
        assert "message_type" in response.text

    def test_role_claim_missing(self, test_payload, assert_missing_claim):
        """The Required role Claim Not Present"""
        assert_missing_claim(
            test_payload,
            "https://purl.imsglobal.org/spec/lti/claim/roles",
            status=403,
        )

    def test_deployment_id_claim_missing(self, test_payload, assert_missing_claim):
        """The Required deployment_id Claim Not Present"""
        assert_missing_claim(
            test_payload,
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id",
            status=403,
        )

    def test_resource_link_id_claim_missing(self, test_payload, assert_missing_claim):
        """The Required resource_link_id Claim Not Present"""
        assert_missing_claim(
            test_payload, "https://purl.imsglobal.org/spec/lti/claim/resource_link"
        )

    def test_user_claim_missing(self, test_payload, assert_missing_claim):
        """The Required sub Claim Not Present"""
        assert_missing_claim(test_payload, "sub", status=403)

    @pytest.fixture(params=["teacher_payload", "student_payload"])
    def test_payload(self, request):
        """Get an OAuthToken or None based on the fixture params."""

        yield request.getfixturevalue(request.param)

    @pytest.fixture(autouse=True)
    def debug_log_capture(self, caplog):
        caplog.set_level(logging.DEBUG)

    @pytest.fixture
    def assert_missing_claim(self, do_lti_launch, make_jwt):
        def _missing_claim(payload, missing_claim, status=422):
            del payload[missing_claim]

            response = do_lti_launch({"id_token": make_jwt(payload)}, status=status)

            assert response.html

            return response

        return _missing_claim
