import uuid
from datetime import datetime, timedelta

from lms.models import LTIRegistration
from lms.services import JWTService


class LTIAHTTPService:
    """Send LTI Advantage requests and return the responses."""

    def __init__(
        self, lti_registration: LTIRegistration, jwt_service: JWTService, http
    ):
        self._lti_registration = lti_registration
        self._jwt_service = jwt_service
        self._http = http

    def sign(self, payload: dict):
        """
        Sign a payload with one of our private keys.

        We include the default values needed for LTIA APIs
        Those default claims are defined here:

            https://www.imsglobal.org/spec/security/v1p0/#id-token
        """
        now = datetime.utcnow()
        payload = {
            "exp": now + timedelta(hours=1),
            "iat": now,
            "nonce": uuid.uuid4().hex,
            "iss": self._lti_registration.client_id,
            "sub": self._lti_registration.client_id,
            "aud": self._lti_registration.issuer,
            **payload,
        }
        return self._jwt_service.encode_with_private_key(payload)

    def request(self, method, url, scopes, headers=None, **kwargs):
        headers = headers or {}

        assert "Authorization" not in headers

        access_token = self._get_access_token(scopes)
        headers["Authorization"] = f"Bearer {access_token}"

        return self._http.request(method, url, headers=headers, **kwargs)

    def _get_access_token(self, scopes):
        """
        Get an access token from the LMS to use in LTA services.

        https://datatracker.ietf.org/doc/html/rfc7523
        https://canvas.instructure.com/doc/api/file.oauth_endpoints.html#post-login-oauth2-token
        """
        signed_jwt = self.sign(
            {
                "aud": self._lti_registration.token_url,
                "jti": uuid.uuid4().hex,
            }
        )

        response = self._http.post(
            self._lti_registration.token_url,
            data={
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": signed_jwt,
                "scope": " ".join(scopes),
            },
        )

        return response.json()["access_token"]


def factory(_context, request):
    return LTIAHTTPService(
        request.find_service(name="application_instance")
        .get_current()
        .lti_registration,
        request.find_service(JWTService),
        request.find_service(name="http"),
    )
