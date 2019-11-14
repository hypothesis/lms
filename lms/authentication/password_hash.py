import binascii
import os
from hashlib import pbkdf2_hmac

__all__ = ["hash_password", "check_password"]


def check_password(password: str, expected_pw_hash: str, salt: str):
    calculated_hash, _ = hash_password(password, salt)

    return calculated_hash == expected_pw_hash.encode("utf8")


def hash_password(pw_to_hash, salt_for_hash: str = ""):
    if isinstance(pw_to_hash, str):
        pw_to_hash = pw_to_hash.encode("utf8")

    if salt_for_hash == "":
        salt_for_hash = binascii.hexlify(os.urandom(8))

    elif isinstance(salt_for_hash, str):
        salt_for_hash = salt_for_hash.encode("utf8")

    hash_pw = binascii.hexlify(
        pbkdf2_hmac("sha256", pw_to_hash, salt_for_hash, 1_000_000)
    )

    return hash_pw, salt_for_hash
