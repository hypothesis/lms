import hashlib
import os
import binascii

if __name__ == "__main__":
    password = input("Please enter a password: ").encode('utf8')
    salt = input("Please enter a salt (leave blank to have one created): ")
    if salt == '':
        salt = binascii.hexlify(os.urandom(8))
    else:
        salt = salt.encode("utf8")

    pw_hash = binascii.hexlify(
        hashlib.pbkdf2_hmac('sha256', password, salt, 1000000)
    )

    print(f"password hash: {pw_hash}")
    print(f"salt: {salt}")
