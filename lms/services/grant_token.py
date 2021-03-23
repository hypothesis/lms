import datetime
from urllib.parse import urlparse

import jwt


class GrantTokenService:
    """
    Service that generates "grant tokens" used to login to the Hypothesis client.

    These tokens are generated in the LMS backend and forwarded to the Hypothesis
    client in assignments via the LMS frontend. The Hypothesis client exchanges
    these tokens for an H API access token which is then used for subsequent API
    requests.

    See https://h.readthedocs.io/en/latest/publishers/authorization-grant-tokens/
    """

    def __init__(
        self, h_api_url_public, h_authority, h_jwt_client_id, h_jwt_client_secret
    ):
        self._h_api_url_public = h_api_url_public
        self._h_authority = h_authority
        self._h_jwt_client_id = h_jwt_client_id
        self._h_jwt_client_secret = h_jwt_client_secret

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
            "exp": now + datetime.timedelta(minutes=5),
        }

        return jwt.encode(
            claims,
            self._h_jwt_client_secret,
            algorithm="HS256",
        )


def factory(_context, request):
    settings = request.registry.settings

    return GrantTokenService(
        h_api_url_public=settings["h_api_url_public"],
        h_authority=settings["h_authority"],
        h_jwt_client_id=settings["h_jwt_client_id"],
        h_jwt_client_secret=settings["h_jwt_client_secret"],
    )
