"""Helpers for working with JWTs. Encapsulates the ``jwt`` lib."""
import copy
import datetime

import jwt

from lms.validation.authentication._exceptions import ExpiredJWTError, InvalidJWTError

__all__ = ["decode_jwt", "encode_jwt"]


def decode_jwt(jwt_str, secret):
    """
    Return the payload decoded from ``jwt_str``.

    :arg jwt_str: the JWT to decode
    :type jwt_str: str
    :arg secret: the secret that ``jwt_str`` was signed with
    :type secret: str

    :raise ExpiredJWTError: if decoding fails because the JWT's timestamp has
        expired
    :raise InvalidJWTError: if decoding fails for any other reason (for example
        ``jwt_str`` is invalid, or ``secret`` is wrong)

    :return: ``jwt_str``'s payload, decoded
    :rtype: dict
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


def encode_jwt(payload, secret):
    """
    Return ``payload`` as a JWT encoded with ``secret``.

    Return a JWT whose payload is ``payload`` and that is signed using
    ``secret``.

    :arg payload: the payload to encode
    :type payload: dict
    :arg secret: the secret to sign the JWT with
    :type secret: str

    :return: the JWT string
    :rtype: str
    """
    payload = copy.deepcopy(payload)
    payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

    jwt_str = jwt.encode(payload, secret, algorithm="HS256")

    return jwt_str
