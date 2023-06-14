from datetime import datetime, timedelta
from typing import List, Optional

from lms.models.jwt_oauth2_token import JWTOAuth2Token


class JWTOAuth2TokenService:
    """Save and retrieve JWTOAuth2Tokens from the DB."""

    EXPIRATION_LEEWAY = 60
    """Allowable wiggle room for expiry time to allow for request's delays."""

    def __init__(self, db):
        self._db = db

    def save(
        self, lti_registration, scopes: List[str], access_token: str, expires_in: int
    ) -> JWTOAuth2Token:
        """
        Save a JWT OAuth2Token to the DB.

        If there's already one for this registration and scopes then overwrite
        its values; otherwise create a new one and add it to the DB.
        """
        token = self.get(lti_registration, scopes, exclude_expired=False)
        if not token:
            token = JWTOAuth2Token(
                lti_registration=lti_registration, scopes=self._normalize_scopes(scopes)
            )
            self._db.add(token)

        token.access_token = access_token
        token.received_at = datetime.now()
        token.expires_at = datetime.now() + timedelta(seconds=expires_in)

        return token

    def get(
        self, lti_registration, scopes: List[str], exclude_expired=True
    ) -> Optional[JWTOAuth2Token]:
        """
        Get a token for the given registration and scopes if present in the DB.

        :param lti_registration: Registration for the token we are looking for
        :param scopes: Scopes of the desired token
        :param exclude_expired: Do not return expired tokens
        """
        query = self._db.query(JWTOAuth2Token).filter(
            JWTOAuth2Token.lti_registration == lti_registration,
            JWTOAuth2Token.scopes == self._normalize_scopes(scopes),
        )
        if exclude_expired:
            query = query.filter(
                (JWTOAuth2Token.expires_at - timedelta(seconds=self.EXPIRATION_LEEWAY))
                >= datetime.now()
            )

        return query.one_or_none()

    def _normalize_scopes(self, scopes: List[str]) -> str:
        """Normalize a list of scopes to be queried/stored in DB."""
        return " ".join(sorted(scopes))


def factory(_context, request):
    return JWTOAuth2TokenService(request.db)
