import copy
import datetime

import jwt

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
