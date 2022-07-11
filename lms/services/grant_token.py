import datetime
from urllib.parse import urlparse

from lms.services.jwt import JWTService


class GrantTokenService:
    """
    Service that generates "grant tokens" used to login to the Hypothesis client.

    These tokens are generated in the LMS backend and forwarded to the Hypothesis
    client in assignments via the LMS frontend. The Hypothesis client exchanges
    these tokens for an H API access token which is then used for subsequent API
    requests.

    See https://h.readthedocs.io/en/latest/publishers/authorization-grant-tokens/
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        h_api_url_public,
        h_authority,
        h_jwt_client_id,
        h_jwt_client_secret,
        jwt_service,
    ):
        self._h_api_url_public = h_api_url_public
        self._h_authority = h_authority
        self._h_jwt_client_id = h_jwt_client_id
        self._h_jwt_client_secret = h_jwt_client_secret
        self._jwt_service = jwt_service

    def generate_token(self, h_user):
        """
        Generate a short-lived login token for a given H user.

        :type h_user: models.HUser
        """

        now = datetime.datetime.utcnow()

        claims = {
            "aud": urlparse(self._h_api_url_public).hostname,
            "iat": now,
            "iss": self._h_jwt_client_id,
            "sub": h_user.userid(self._h_authority),
            "nbf": now,
        }

        return self._jwt_service.encode_with_secret(
            claims, self._h_jwt_client_secret, lifetime=datetime.timedelta(minutes=5)
        )


def factory(_context, request):
    settings = request.registry.settings

    return GrantTokenService(
        h_api_url_public=settings["h_api_url_public"],
        h_authority=settings["h_authority"],
        h_jwt_client_id=settings["h_jwt_client_id"],
        h_jwt_client_secret=settings["h_jwt_client_secret"],
        jwt_service=request.find_service(JWTService),
    )
