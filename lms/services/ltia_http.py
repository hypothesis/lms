import logging
import uuid
from datetime import datetime, timedelta

from requests.exceptions import JSONDecodeError

from lms.models import JWTOAuth2Token, LTIRegistration
from lms.product.plugin.misc import MiscPlugin
from lms.services.exceptions import SerializableError
from lms.services.jwt import JWTService
from lms.services.jwt_oauth2_token import JWTOAuth2TokenService

LOG = logging.getLogger(__name__)


class LTIAHTTPService:
    """Send LTI Advantage requests and return the responses."""

    def __init__(
        self,
        plugin: MiscPlugin,
        jwt_service: JWTService,
        http,
        jwt_oauth2_token_service: JWTOAuth2TokenService,
    ):
        self._jwt_service = jwt_service
        self._http = http
        self._plugin = plugin
        self._jwt_oauth2_token_service = jwt_oauth2_token_service

    def request(
        self,
        lti_registration: LTIRegistration,
        method,
        url,
        scopes,
        headers=None,
        **kwargs,
    ):
        headers = headers or {}

        assert "Authorization" not in headers  # noqa: S101

        access_token = self._get_access_token(lti_registration, scopes)
        headers["Authorization"] = f"Bearer {access_token}"

        return self._http.request(method, url, headers=headers, **kwargs)

    def _get_access_token(
        self, lti_registration: LTIRegistration, scopes: list[str]
    ) -> str:
        """Get a valid access token from the DB or get a new one from the LMS."""
        token = self._jwt_oauth2_token_service.get_token(lti_registration, scopes)
        if not token:
            LOG.debug("Requesting new LTIA JWT token")
            token = self._get_new_access_token(lti_registration, scopes)
        else:
            LOG.debug("Using cached LTIA JWT token")

        return token.access_token

    def _get_new_access_token(
        self, lti_registration: LTIRegistration, scopes: list[str]
    ) -> JWTOAuth2Token:
        """
        Get an access token from the LMS to use in LTA services.

        https://datatracker.ietf.org/doc/html/rfc7523
        https://canvas.instructure.com/doc/api/file.oauth_endpoints.html#post-login-oauth2-token
        """
        now = datetime.utcnow()  # noqa: DTZ003
        signed_jwt = self._jwt_service.encode_with_private_key(
            {
                "exp": now + timedelta(hours=1),
                "iat": now,
                "iss": lti_registration.client_id,
                "sub": lti_registration.client_id,
                "aud": self._plugin.get_ltia_aud_claim(lti_registration),
                "jti": uuid.uuid4().hex,
            }
        )

        response = self._http.post(
            lti_registration.token_url,
            data={
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": signed_jwt,
                "scope": " ".join(scopes),
            },
            timeout=(30, 30),
        )

        try:
            token_data = response.json()
        except JSONDecodeError as err:  # pragma: no cover
            LOG.error("Non-json response: %s", response.text)  # noqa: TRY400
            raise SerializableError(  # noqa: TRY003
                "Non JSON response from LTI1.3 token endpoint.",  # noqa: EM101
                details={"token_url": lti_registration.token_url},
            ) from err

        token = self._jwt_oauth2_token_service.save_token(
            lti_registration=lti_registration,
            scopes=scopes,
            access_token=token_data["access_token"],
            expires_in=token_data["expires_in"],
        )
        return token


def factory(_context, request):
    return LTIAHTTPService(
        request.product.plugin.misc,
        request.find_service(JWTService),
        request.find_service(name="http"),
        request.find_service(JWTOAuth2TokenService),
    )
