import copy
import datetime
import logging
from functools import lru_cache

import jwt
import requests
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError

from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.services.lti_registration import LTIRegistrationService
from lms.services.rsa_key import RSAKeyService
from lms.validation import ValidationError

LOG = logging.getLogger(__name__)


class JWTService:
    LEEWAY = datetime.timedelta(seconds=10)
    """
    Leeway to allow for timestamp fields when decoding JWTs.

    This accounts for small clock differences between the server generating the
    JWT and us.
    """

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
                jwt_str,
                secret,
                algorithms=["HS256"],
                options={"require": ["exp"]},
                leeway=cls.LEEWAY,
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

        try:
            unverified_header = jwt.get_unverified_header(id_token)
            unverified_payload = jwt.decode(
                id_token, options={"verify_signature": False}
            )
        except PyJWTError as err:
            LOG.debug("Invalid JWT. %s", str(err))
            raise ValidationError(messages={"jwt": [f"Invalid JWT. {err}"]}) from err

        if not unverified_header.get("kid"):
            LOG.debug("Missing 'kid' value in JWT header")
            raise ValidationError(
                messages={"jwt": ["Missing 'kid' value in JWT header"]}
            )

        iss, aud = unverified_payload.get("iss"), unverified_payload.get("aud")
        # Find the registration based on the token's claimed issuer & audience
        registration = self._registration_service.get(iss, aud)
        if not registration:
            LOG.debug("Unknown registration for lti_token. iss:%s aud:%s.", iss, aud)
            raise ValidationError(
                messages={
                    "jwt": [f"Unknown registration for JWT. iss:{iss} aud:{aud}."]
                }
            )

        try:
            signing_key = self._get_jwk_client(
                registration.key_set_url
            ).get_signing_key_from_jwt(id_token)

            return jwt.decode(
                id_token,
                key=signing_key.key,
                audience=aud,
                algorithms=["RS256"],
                leeway=self.LEEWAY,
            )
        except PyJWTError as err:
            LOG.debug("Invalid JWT for: %s, %s. %s", iss, aud, str(err))
            raise ValidationError(
                messages={"jwt": [f"Invalid JWT for: {iss}, {aud}. {err}"]}
            ) from err

    def encode_with_private_key(self, payload: dict):
        key = self._rsa_key_service.get_random_key()
        return jwt.encode(
            payload,
            self._rsa_key_service.private_key(key),
            algorithm="RS256",
            headers={"kid": key.kid},
        )

    @staticmethod
    @lru_cache(maxsize=256)
    def _get_jwk_client(jwk_url: str):
        """
        Get a PyJWKClient for the given key set URL.

        PyJWKClient maintains a cache of keys it has seen.
        We want to keep the clients around with `lru_cache` to reuse that internal cache.
        """
        return _RequestsPyJWKClient(jwk_url, cache_keys=True)


class _RequestsPyJWKClient(jwt.PyJWKClient):
    """
    Version of PyJWKClient which uses requests to gather JWKs.

    Having our own class and using request allows for easier customization.
    """

    def fetch_data(self):
        # We found that some Moodle instances return 403s
        # on request without an User-Agent.
        with requests.get(
            self.uri, headers={"User-Agent": "requests"}, timeout=(10, 10)
        ) as response:
            return response.json()


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
