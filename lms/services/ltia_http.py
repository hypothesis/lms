import uuid
from datetime import datetime, timedelta

from lms.models import LTIRegistration
from lms.product.plugin.misc import MiscPlugin
from lms.services.jwt import JWTService


class LTIAHTTPService:
    """Send LTI Advantage requests and return the responses."""

    def __init__(
        self,
        lti_registration: LTIRegistration,
        plugin: MiscPlugin,
        jwt_service: JWTService,
        http,
    ):
        self._lti_registration = lti_registration
        self._jwt_service = jwt_service
        self._http = http
        self._plugin = plugin

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
        now = datetime.utcnow()
        signed_jwt = self._jwt_service.encode_with_private_key(
            {
                "exp": now + timedelta(hours=1),
                "iat": now,
                "iss": self._lti_registration.client_id,
                "sub": self._lti_registration.client_id,
                "aud": self._plugin.get_ltia_aud_claim(self._lti_registration),
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
    lti_registration = (
        request.find_service(name="application_instance").get_current().lti_registration
    )

    return LTIAHTTPService(
        lti_registration,
        request.product.plugin.misc,
        request.find_service(JWTService),
        request.find_service(name="http"),
    )
