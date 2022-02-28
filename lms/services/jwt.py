import jwt
import uuid
import time

from lms.services import KeyService


class JWTService:
    def __init__(self, key_service, aes_secret, http, oauth2):
        self._key_service = key_service
        self._aes_secret = aes_secret
        self._http = http
        self._ouath2 = oauth2

    def sign(self, registration, message):
        now = int(time.time())

        key = self._key_service.one()
        message.update(
            {
                "aud": registration.issuer,
                "exp": now + 60 * 60,
                "iat": now - 25,
                "nonce": uuid.uuid4().hex,
                "iss": registration.client_id,
            }
        )

        headers = {"kid": key.kid.hex}

        return jwt.encode(
            message,
            key.private_key(self._aes_secret),
            algorithm="RS256",
            headers=headers,
        )


def factory(_context, request):
    return JWTService(
        request.find_service(KeyService),
        request.registry.settings["aes_secret"],
        # From here things might belong to another http service
        request.find_service(name="http"),
        request.find_service(name="oauth2_token"),
    )
