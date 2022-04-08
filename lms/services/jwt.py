import copy
import datetime
from functools import lru_cache

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError

from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.services.lti_registration import LTIRegistrationService


class JWTService:
    def __init__(self, registration_service):
        self._registration_service = registration_service

    @classmethod
    def decode_with_secret(cls, jwt_str, secret) -> dict:
        """
        Decode the payload decoded from `jwt_str`.

        :param jwt_str: JWT to decode
        :param secret: secret used for decoding

        :raise ExpiredJWTError: if decoding fails because the JWT's timestamp has
            expired
        :raise InvalidJWTError: if decoding fails for any other reason (for example
            `jwt_str` is invalid, or `secret` is wrong)

        :return: `jwt_str`'s payload, decoded
        """
        try:
            payload = jwt.decode(
                jwt_str, secret, algorithms=["HS256"], options={"require": ["exp"]}
            )
        except ExpiredSignatureError as err:
            raise ExpiredJWTError() from err
        except InvalidTokenError as err:
            raise InvalidJWTError() from err

        del payload["exp"]
        return payload

    @classmethod
    def encode_with_secret(cls, payload: dict, secret, lifetime):
        """
        Encode `payload` as a JWT.

        :param payload: payload to encode
        :param secret: secret used for encoding
        :param lifetime: how long the token should be valid for

        :return: the JWT string
        """
        payload = copy.deepcopy(payload)
        payload["exp"] = datetime.datetime.utcnow() + lifetime

        jwt_str = jwt.encode(payload, secret, algorithm="HS256")

        return jwt_str

    @staticmethod
    @lru_cache
    def _get_jwk_client(jwk_url: str):
        """
        Get a PyJWKClient for the given key set URL.

        PyJWKClient maintains a cache of keys it has seen we want to keep
        the clients around with `lru_cache` in case we can reuse that internal cache
        """
        return jwt.PyJWKClient(jwk_url)

    def decode_lti_token(self, id_token):
        header = jwt.get_unverified_header(id_token)
        if not header.get("kid"):
            raise InvalidJWTError("Missing 'kid' value in JWT header")

        unverified_payload = jwt.decode(id_token, options={"verify_signature": False})
        iss, aud = unverified_payload.get("iss"), unverified_payload.get("aud")

        registration = self._registration_service.get(iss, aud)
        if not registration:
            raise InvalidJWTError(
                f"Unknown registration for lti_token. iss:'{iss}' aud:'{aud}'."
            )

        try:
            signing_key = self._get_jwk_client(
                registration.key_set_url
            ).get_signing_key_from_jwt(id_token)

            return jwt.decode(
                id_token, key=signing_key.key, audience=aud, algorithms=["RS256"]
            )
        except PyJWTError as err:
            raise InvalidJWTError(str(err)) from err


def factory(_context, request):
    return JWTService(registration_service=request.find_service(LTIRegistrationService))
