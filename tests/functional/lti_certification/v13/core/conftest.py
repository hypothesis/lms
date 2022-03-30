import pytest

from tests import factories


@pytest.fixture(autouse=True)
def lti_registration(db_session):  # pylint:disable=unused-argument
    return factories.LTIRegistration(
        issuer="https://ltiadvantagevalidator.imsglobal.org",
        client_id="imstester_4ba76ab",
    )


@pytest.fixture(autouse=True)
def applicaiton_instance(lti_registration):  # pylint:disable=unused-argument
    return factories.ApplicationInstance(
        lti_registration=lti_registration, deployment_id="testdeploy"
    )


@pytest.fixture
def student_payload():
    return {
        "iss": "https://ltiadvantagevalidator.imsglobal.org",
        "sub": "STUDENT_ID",
        "aud": "imstester_4ba76ab",
        "exp": 1648638014,
        "iat": 1648637714,
        "nonce": "d45a2497-4389-45ea-8d61-b1fa7e407447",
        "name": "STUDENT_FIRST_NAME STUDENT_MIDDLE_NAME STUDENT_LAST_NAME",
        "given_name": "STUDENT_FIRST_NAME",
        "family_name": "STUDENT_LAST_NAME",
        "middle_name": "STUDENT_MIDDLE_NAME",
        "email": "student@email.com",
        "locale": "en-US",
        "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": "https://localhost/lti_launches",
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "testdeploy",
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
        "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
        "https://purl.imsglobal.org/spec/lti/claim/roles": [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"
        ],
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
    }


@pytest.fixture
def teacher_payload():
    return {
        "iss": "https://ltiadvantagevalidator.imsglobal.org",
        "sub": "TEACHER_ID",
        "aud": "imstester_4ba76ab",
        "exp": 1648638333,
        "iat": 1648638033,
        "nonce": "6f889151-c368-4e32-91af-5fe831ee266b",
        "name": "TEACHER_FIRST_NAME TEACHER_MIDDLE_NAME TEACHER_LAST_NAME",
        "given_name": "TEACHER_FIRST_NAME",
        "family_name": "TEACHER_LAST_NAME",
        "middle_name": "TEACHER_MIDDLE_NAME",
        "email": "teacher@email.com",
        "locale": "en-US",
        "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": "https://localhost/lti_launches",
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "testdeploy",
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
        "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
        "https://purl.imsglobal.org/spec/lti/claim/roles": [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor"
        ],
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
    }
