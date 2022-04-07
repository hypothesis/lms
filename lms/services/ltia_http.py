import uuid
from datetime import datetime, timedelta

from lms.services import JWTService


class LTIAHTTPService:
    """Send LTI Advantage requests and return the responses."""

    def __init__(self, lti_registration, jwt_service, http):
        self._lti_registration = lti_registration
        self._jwt_service = jwt_service
        self._http = http

    def _sign(self, registration, payload, lifetime=timedelta(hours=1)):
        now = datetime.utcnow()
        default_payload = {
            "exp": now + lifetime,
            "iat": now,
            "nonce": uuid.uuid4().hex,
            "iss": registration.client_id,
            "sub": registration.client_id,
        }
        payload = dict(default_payload, **payload)

        return self._jwt_service.encode_with_private_key(payload)

    def _get_access_token(self, scopes):
        """
        Get an access token from the LMS to use in LTA services.

        https://datatracker.ietf.org/doc/html/rfc7523
        https://canvas.instructure.com/doc/api/file.oauth_endpoints.html#post-login-oauth2-token
        """
        jwt = self._sign(
            self._lti_registration,
            {
                "jti": uuid.uuid4().hex,
                "aud": self._lti_registration.token_url,
            },
        )
        auth_request = {
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": jwt,
            "scope": " ".join(scopes),
        }
        response = self._http.post(
            self._lti_registration.token_url,
            data=auth_request,
        )
        return response.json()["access_token"]

    def request(self, scopes, method, url, headers=None, **kwargs):
        headers = headers or {}

        assert "Authorization" not in headers

        access_token = self._get_access_token(scopes)
        headers["Authorization"] = f"Bearer {access_token}"

        return self._http.request(method, url, headers=headers, **kwargs)


def factory(_context, request):
    return LTIAHTTPService(
        request.find_service(name="application_instance")
        .get_current()
        .lti_registration,
        request.find_service(JWTService),
        request.find_service(name="http"),
    )
