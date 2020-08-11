#!/usr/bin/env python3
from lms.authentication.password_hash import hash_password

if __name__ == "__main__":
    password = input("Please enter a password: ").encode("utf8")
    salt = input("Please enter a salt (leave blank to have one created): ")

    pw_hash, salt = hash_password(password, salt)

    print(f"password hash: {pw_hash}")
    print(f"salt: {salt}")
