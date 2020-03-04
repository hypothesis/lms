"""Functions for hashing and checking passwords."""

import binascii
import os
from hashlib import pbkdf2_hmac

__all__ = ["hash_password", "check_password"]


def check_password(password: str, expected_hash: str, salt: str):
    """
    Check that a password matches the expected hash.

    :param password: The password to check
    :param expected_hash: The expected hash
    :param salt: The salt used to generate the hash
    :rtype: bool
    :return: Does these credentials match?
    """
    calculated_hash, _ = hash_password(password, salt)

    return calculated_hash == expected_hash.encode("utf8")


def hash_password(password: str, salt: str = None):
    """
    Create a hash and possibly salt for a password.

    :param password: The password to hash
    :param salt: An optional salt. If this is not passed, then a random salt
                 will be generated.
    :return: A tuple of hash and salt
    """
    if isinstance(password, str):
        password = password.encode("utf8")

    if not salt:
        salt = binascii.hexlify(os.urandom(8))

    elif isinstance(salt, str):
        salt = salt.encode("utf8")

    hash_pw = binascii.hexlify(pbkdf2_hmac("sha256", password, salt, 1_000_000))

    return hash_pw, salt
