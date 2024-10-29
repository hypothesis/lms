from datetime import datetime, timedelta

from lms.models.jwt_oauth2_token import JWTOAuth2Token


class JWTOAuth2TokenService:
    """Save and retrieve JWTOAuth2Tokens from the DB."""

    EXPIRATION_LEEWAY = 60
    """Allowable wiggle room for expiry time to allow for request's delays."""

    def __init__(self, db):
        self._db = db

    def save_token(
        self, lti_registration, scopes: list[str], access_token: str, expires_in: int
    ) -> JWTOAuth2Token:
        """
        Save a JWT OAuth2Token to the DB.

        If there's already one for this registration and scopes then overwrite
        its values; otherwise create a new one and add it to the DB.
        """
        token = self.get_token(lti_registration, scopes, exclude_expired=False)
        if not token:
            token = JWTOAuth2Token(
                lti_registration=lti_registration, scopes=self._normalize_scopes(scopes)
            )
            self._db.add(token)

        token.access_token = access_token
        token.expires_at = datetime.now() + timedelta(seconds=expires_in)

        return token

    def get_token(
        self, lti_registration, scopes: list[str], exclude_expired=True
    ) -> JWTOAuth2Token | None:
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

    def _normalize_scopes(self, scopes: list[str]) -> str:
        """Normalize a list of scopes to be queried/stored in DB."""
        return " ".join(sorted(scopes))


def factory(_context, request):
    return JWTOAuth2TokenService(request.db)
