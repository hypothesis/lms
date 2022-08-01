import json
from datetime import datetime

import httpretty
import importlib_resources
import jwt
import pytest
from pytest import register_assert_rewrite

from tests import factories

# Ensure that assertions get nice formatting from pytest
register_assert_rewrite("tests.function.lti_certification.v13.assertions")

keys_path = importlib_resources.files("tests.functional.lti_certification.v13")


@pytest.fixture(scope="session")
def jwt_private_key():
    return (keys_path / "jwt_private.key").read_text()


@pytest.fixture(scope="session")
def jwt_public_key():
    key = json.loads((keys_path / "jwt_public.key").read_text())
    key["kid"] = "TESTING_KID"
    return key


@pytest.fixture
def jwt_headers(jwt_public_key):
    return {"kid": jwt_public_key["kid"]}


@pytest.fixture
def make_jwt(jwt_headers, jwt_private_key):
    def _make_jwt(payload, headers=None):
        if not headers:
            headers = jwt_headers

        return jwt.encode(payload, jwt_private_key, algorithm="RS256", headers=headers)

    return _make_jwt


@pytest.fixture(autouse=True)
def lti_registration(db_session):  # pylint:disable=unused-argument
    return factories.LTIRegistration(
        issuer="https://ltiadvantagevalidator.imsglobal.org",
        client_id="imstester_4ba76ab",
        key_set_url="https://oauth2server.imsglobal.org/jwks",
        token_url="https://ltiadvantagevalidator.imsglobal.org/ltitool/authcodejwt.html",
    )


@pytest.fixture(autouse=True)
def application_instance(lti_registration):
    return factories.ApplicationInstance(
        tool_consumer_instance_guid="TEST_CONSUMER_INSTANCE_GUID",
        lti_registration=lti_registration,
        deployment_id="testdeploy",
    )


@pytest.fixture(autouse=True)
def mock_http_jwt_endpoint(lti_registration, jwt_public_key):
    """Mock the response of the platform's JWT HTTP end-point."""
    jwk = {"keys": [jwt_public_key]}

    with httpretty.enabled():
        httpretty.register_uri(
            method="GET", uri=lti_registration.key_set_url, body=json.dumps(jwk)
        )

        yield


@pytest.fixture
def student_payload(common_payload):
    return {
        "sub": "STUDENT_ID",
        "nonce": "d45a2497-4389-45ea-8d61-b1fa7e407447",
        "name": "STUDENT_FIRST_NAME STUDENT_MIDDLE_NAME STUDENT_LAST_NAME",
        "given_name": "STUDENT_FIRST_NAME",
        "family_name": "STUDENT_LAST_NAME",
        "middle_name": "STUDENT_MIDDLE_NAME",
        "email": "student@email.com",
        "https://purl.imsglobal.org/spec/lti/claim/roles": [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"
        ],
        **common_payload,
    }


@pytest.fixture
def teacher_payload(common_payload):
    return {
        "sub": "TEACHER_ID",
        "nonce": "6f889151-c368-4e32-91af-5fe831ee266b",
        "name": "TEACHER_FIRST_NAME TEACHER_MIDDLE_NAME TEACHER_LAST_NAME",
        "given_name": "TEACHER_FIRST_NAME",
        "family_name": "TEACHER_LAST_NAME",
        "middle_name": "TEACHER_MIDDLE_NAME",
        "email": "teacher@email.com",
        "https://purl.imsglobal.org/spec/lti/claim/roles": [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor"
        ],
        **common_payload,
    }


@pytest.fixture
def common_payload():
    # This is the parts of the payload common to both teacher and student
    now = int(datetime.timestamp(datetime.now()))

    return {
        "exp": now + 60,
        "iat": now,
        "iss": "https://ltiadvantagevalidator.imsglobal.org",
        "aud": "imstester_4ba76ab",
        "locale": "en-US",
        "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": "https://localhost/lti_launches",
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "testdeploy",
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
        "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
        "https://purl.imsglobal.org/spec/lti/claim/context": {
            "id": "COURSE_ID",
            "label": "COURSE_LABEL",
            "title": "COURSE_TITLE",
            "type": ["http://purl.imsglobal.org/vocab/lis/v2/course#CourseSection"],
        },
        "https://purl.imsglobal.org/spec/lti/claim/resource_link": {
            "id": "RESOURCE_ID",
            "title": "Introduction Assignment",
            "description": "This is the introduction assignment",
        },
        "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice": {
            "context_memberships_url": "https://ltiadvantagevalidator.imsglobal.org/ltitool/namesandroles.html?memberships=10843",
            "service_versions": ["2.0"],
        },
        "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint": {
            "scope": [
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
                "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
                "https://purl.imsglobal.org/spec/lti-ags/scope/score",
            ],
            "lineitems": "https://ltiadvantagevalidator.imsglobal.org/ltitool/rest/assignmentsgrades/10843/lineitems",
        },
        "https://purl.imsglobal.org/spec/lti/claim/custom": {
            "canvas_user_id": 1000,
            # Mirror the custom param we set in the LTI compliance testing tool
            # This gets around the fact it doesn't send a GUID by default
            "certification_guid": "TEST_CONSUMER_INSTANCE_GUID",
        },
    }
