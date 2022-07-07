import pytest

from lms.models.lti_registration import LTIRegistration


@pytest.mark.parametrize(
    "issuer,client_id,expected",
    [
        (
            "https://blackboard.com",
            "CLIENT_ID",
            {
                "auth_login_url": "https://developer.blackboard.com/api/v1/gateway/oidcauth",
                "key_set_url": "https://developer.blackboard.com/api/v1/management/applications/CLIENT_ID/jwks.json",
                "token_url": "https://developer.blackboard.com/api/v1/gateway/oauth2/jwttoken",
            },
        ),
        (
            "https://hypothesis.instructure.com",
            "client_id",
            {
                "auth_login_url": "https://canvas.instructure.com/api/lti/authorize_redirect",
                "key_set_url": "https://canvas.instructure.com/api/lti/security/jwks",
                "token_url": "https://canvas.instructure.com/login/oauth2/token",
            },
        ),
        (
            "https://hypothesis.brightspace.com",
            "client_id",
            {
                "auth_login_url": "https://hypothesis.brightspace.com/d2l/lti/authenticate",
                "key_set_url": "https://hypothesis.brightspace.com/d2l/.well-known/jwks",
                "token_url": "https://hypothesis.brightspace.com/core/connect/token",
            },
        ),
        (
            "https://hypothesis.moodlecloud.com",
            "client_id",
            {
                "auth_login_url": "https://hypothesis.moodlecloud.com/mod/lti/auth.php",
                "key_set_url": "https://hypothesis.moodlecloud.com/mod/lti/certs.php",
                "token_url": "https://hypothesis.moodlecloud.com/mod/lti/certs.php",
            },
        ),
        (
            "https://unknown.lms.com",
            "client_id",
            {"auth_login_url": None, "key_set_url": None, "token_url": None},
        ),
    ],
)
def test_urls(issuer, client_id, expected):
    assert LTIRegistration.urls(issuer, client_id) == expected
