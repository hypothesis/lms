#!/usr/bin/env python
# Requires python 3.6+

import hashlib
import os
import binascii


def get_hash(pw_to_hash, salt_for_hash: str = ''):
    if isinstance(pw_to_hash, str):
        pw_to_hash = pw_to_hash.encode("utf8")
    if salt_for_hash == '':
        salt_for_hash = binascii.hexlify(os.urandom(8))
    elif isinstance(salt_for_hash, str):
        salt_for_hash = salt_for_hash.encode("utf8")

    hash_pw = binascii.hexlify(
        hashlib.pbkdf2_hmac('sha256', pw_to_hash, salt_for_hash, 1000000))

    return hash_pw, salt_for_hash


if __name__ == "__main__":
    # pylint: disable=invalid-name
    password = input("Please enter a password: ").encode('utf8')
    salt = input("Please enter a salt (leave blank to have one created): ")

    pw_hash, salt = get_hash(password, salt)

    print(f"password hash: {pw_hash}")
    print(f"salt: {salt}")
