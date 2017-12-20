import secrets
from datetime import datetime
from Crypto.Cipher import AES
from Crypto import Random

import sqlalchemy as sa
from lms.db import BASE

# TODO we should figure out a more standard place to set this
LTI_KEY_BASE = "Hypothesis"


def build_aes_iv():
    """Build a 16 byte initialization vector."""
    return Random.new().read(AES.block_size)


def encrypt_oauth_secret(oauth_secret, key, init_v):
    """Encrypt an oauth secrety via AES encryption."""
    cipher = AES.new(key, AES.MODE_CFB, init_v)
    return cipher.encrypt(oauth_secret)


def decrypt_oauth_secret(encrypted_secret, key, init_v):
    """Decrypt AES encrypted secret."""
    cipher = AES.new(key, AES.MODE_CFB, init_v)
    return cipher.decrypt(encrypted_secret)


class ApplicationInstance(BASE):
    """Class to represent a single lms install."""

    __tablename__ = 'application_instances'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    consumer_key = sa.Column(sa.String)
    shared_secret = sa.Column(sa.String)
    lms_url = sa.Column(sa.String(2048))
    requesters_email = sa.Column(sa.String(2048))
    created = sa.Column(sa.TIMESTAMP, default=datetime.utcnow())
    developer_key = sa.Column(sa.String)
    developer_secret = sa.Column(sa.LargeBinary, default=None)
    aes_cipher_iv = sa.Column(sa.LargeBinary, default=None)

    def decrypted_developer_secret(self, key):
        encrypted_secret = self.developer_secret
        return decrypt_oauth_secret(encrypted_secret, key, self.aes_cipher_iv)


def find_by_oauth_consumer_key(session, key):
    return session.query(ApplicationInstance).filter(
        ApplicationInstance.consumer_key == key).one_or_none()


def build_shared_secret():
    """Generate a shared secrect."""
    return secrets.token_hex(64)


def build_unique_key():
    """Use the key base to generate lms key."""
    return LTI_KEY_BASE + secrets.token_hex(16)


def build_from_lms_url(lms_url, email, developer_key,
                       developer_secret, encryption_key=None):
    """Intantiate ApplicationIntance with lms_url."""
    encrypted_secret = developer_secret
    aes_iv = None
    if encryption_key is not None and developer_secret and developer_key:
        aes_iv = build_aes_iv()
        encrypted_secret = encrypt_oauth_secret(developer_secret, encryption_key, aes_iv)

    return ApplicationInstance(
        consumer_key=build_unique_key(),
        shared_secret=build_shared_secret(),
        lms_url=lms_url,
        requesters_email=email,
        developer_key=developer_key,
        developer_secret=encrypted_secret,
        aes_cipher_iv=aes_iv,
    )
