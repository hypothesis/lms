import copy
import datetime
from functools import lru_cache

import jwt
from jwt import PyJWKClient

from lms.services.exceptions import ExpiredJWTError, InvalidJWTError


class JWTService:
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
        except jwt.ExpiredSignatureError as err:
            raise ExpiredJWTError() from err
        except jwt.InvalidTokenError as err:
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

    @classmethod
    def decode_unverified(cls, jwt_str):
        """Decode a JWT token without any verification."""
        return jwt.decode(jwt_str, options={"verify_signature": False})

    @staticmethod
    @lru_cache
    def _get_jwk_client(jwk_url: str) -> PyJWKClient:
        """
        Get a PyJWKClient for the given key set URL.

        PyJWKClient maintains a cache of keys it has seen we want to keep
        the clients around with `lru_cache` in case we can reuse that internal cache
        """
        return PyJWKClient(jwk_url)

    @classmethod
    def decode_with_jwk_url(cls, jwt_str, jwk_url: str, audience: str):
        """Decode a JWK verifying against the public key published at `jwk_url`."""
        header = jwt.get_unverified_header(jwt_str)
        if not header.get("kid"):
            raise InvalidJWTError("Missing 'kid' value in JWT header")

        signing_key = cls._get_jwk_client(jwk_url).get_signing_key_from_jwt(jwt_str)
        try:
            payload = jwt.decode(
                jwt_str, key=signing_key.key, audience=audience, algorithms=["RS256"]
            )
        except jwt.exceptions.InvalidTokenError as err:
            raise InvalidJWTError() from err

        return payload
