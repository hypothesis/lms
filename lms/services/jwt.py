import copy
import datetime
import logging
from functools import lru_cache

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError

from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.services.lti_registration import LTIRegistrationService
from lms.services.rsa_key import RSAKeyService

LOG = logging.getLogger(__name__)


class JWTService:
    def __init__(self, registration_service, rsa_key_service):
        self._registration_service = registration_service
        self._rsa_key_service = rsa_key_service

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

    def decode_lti_token(self, id_token: str) -> dict:
        """
        Decode an LTI `id_token` JWT.

        The JWT is validated against its corresponding LTIRegistration public key
        """
        if not id_token:
            return {}

        if not jwt.get_unverified_header(id_token).get("kid"):
            LOG.debug("Missing 'kid' value in JWT header")
            return {}

        unverified_payload = jwt.decode(id_token, options={"verify_signature": False})
        iss, aud = unverified_payload.get("iss"), unverified_payload.get("aud")

        # Find the registration based on the token's claimed issuer & audience
        registration = self._registration_service.get(iss, aud)
        if not registration:
            LOG.debug("Unknown registration for lti_token. iss:%s aud:%s.", iss, aud)
            return {}

        try:
            signing_key = self._get_jwk_client(
                registration.key_set_url
            ).get_signing_key_from_jwt(id_token)

            return jwt.decode(
                id_token, key=signing_key.key, audience=aud, algorithms=["RS256"]
            )
        except PyJWTError as err:
            LOG.debug("Invalid JWT. %s", str(err))
            return {}

    def encode_with_private_key(self, payload: dict):
        key = self._rsa_key_service.get_random_key()
        headers = {"kid": key.kid}

        return jwt.encode(
            payload,
            self._rsa_key_service.private_key(key),
            algorithm="RS256",
            headers=headers,
        )

    @staticmethod
    @lru_cache
    def _get_jwk_client(jwk_url: str):
        """
        Get a PyJWKClient for the given key set URL.

        PyJWKClient maintains a cache of keys it has seen we want to keep
        the clients around with `lru_cache` in case we can reuse that internal cache
        """
        return jwt.PyJWKClient(jwk_url)


def factory(_context, request):
    return JWTService(
        registration_service=request.find_service(LTIRegistrationService),
        rsa_key_service=request.find_service(RSAKeyService),
    )


def _get_lti_jwt(request):
    return request.find_service(JWTService).decode_lti_token(
        request.params.get("id_token")
    )


def includeme(config):
    config.add_request_method(_get_lti_jwt, name="lti_jwt", property=True, reify=True)
