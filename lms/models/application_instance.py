import secrets
from datetime import datetime
from urllib.parse import urlparse

import sqlalchemy as sa
from Cryptodome import Random
from Cryptodome.Cipher import AES
from sqlalchemy.dialects.postgresql import JSONB

from lms.db import BASE
from lms.models.application_settings import ApplicationSettings


class ApplicationInstance(BASE):
    """Class to represent a single lms install."""

    __tablename__ = "application_instances"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    consumer_key = sa.Column(sa.String, unique=True, nullable=False)
    shared_secret = sa.Column(sa.String, nullable=False)
    lms_url = sa.Column(sa.String(2048), nullable=False)
    requesters_email = sa.Column(sa.String(2048), nullable=False)
    created = sa.Column(sa.TIMESTAMP, default=datetime.utcnow(), nullable=False)
    developer_key = sa.Column(sa.String)
    developer_secret = sa.Column(sa.LargeBinary)
    aes_cipher_iv = sa.Column(sa.LargeBinary)
    provisioning = sa.Column(
        sa.Boolean(),
        default=True,
        server_default=sa.sql.expression.true(),
        nullable=False,
    )

    settings = sa.Column(
        "settings",
        ApplicationSettings.as_mutable(JSONB),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )

    #: A list of all the OAuth2Tokens for this application instance
    #: (each token belongs to a different user of this application
    #: instance's LMS).
    access_tokens = sa.orm.relationship(
        "OAuth2Token", back_populates="application_instance"
    )

    #: A list of all the courses for this application instance.
    courses = sa.orm.relationship("Course", back_populates="application_instance")

    #: A list of all the GroupInfo's for this application instance.
    group_infos = sa.orm.relationship(
        "GroupInfo", back_populates="application_instance"
    )

    def decrypted_developer_secret(self, aes_secret):
        if self.developer_secret is None:
            return None

        cipher = AES.new(aes_secret, AES.MODE_CFB, self.aes_cipher_iv)

        return cipher.decrypt(self.developer_secret)

    def lms_host(self):
        """
        Return the hostname part of this ApplicationInstance's lms_url.

        For example if application_instance.lms_url is
        "https://example.com/lms/" then application_instance.lms_host() will
        return "example.com".

        :raise ValueError: if the ApplicationInstance's lms_url can't be parsed
        """
        # urlparse() or .netloc will raise ValueError for some invalid URLs.
        lms_host = urlparse(self.lms_url).netloc

        # For some URLs urlparse(url).netloc returns an empty string.
        if not lms_host:
            raise ValueError(
                f"Couldn't parse self.lms_url ({self.lms_url}): urlparse() returned an empty netloc"
            )

        return lms_host

    @classmethod
    def get_by_consumer_key(cls, db, consumer_key):
        """Return the ApplicationInstance with the given consumer_key or None."""
        return db.query(cls).filter_by(consumer_key=consumer_key).one_or_none()

    @classmethod
    def build_from_lms_url(  # pylint:disable=too-many-arguments
        cls, lms_url, email, developer_key, developer_secret, encryption_key, settings
    ):
        """Instantiate ApplicationInstance with lms_url."""
        encrypted_secret = developer_secret
        aes_iv = None
        if developer_secret and developer_key:
            aes_iv = _build_aes_iv()
            encrypted_secret = _encrypt_oauth_secret(
                developer_secret, encryption_key, aes_iv
            )

        return cls(
            consumer_key=_build_unique_key(),
            shared_secret=_build_shared_secret(),
            lms_url=lms_url,
            requesters_email=email,
            developer_key=developer_key,
            developer_secret=encrypted_secret,
            aes_cipher_iv=aes_iv,
            created=datetime.utcnow(),
            settings=settings,
        )


def _build_aes_iv():
    """Build a 16 byte initialization vector."""
    return Random.new().read(AES.block_size)


def _build_shared_secret():
    """Generate a shared secret."""
    return secrets.token_hex(32)


def _build_unique_key():
    """Use the key base to generate lms key."""
    return "Hypothesis" + secrets.token_hex(16)


def _encrypt_oauth_secret(oauth_secret, key, init_v):
    """Encrypt an oauth secrety via AES encryption."""

    if isinstance(oauth_secret, str):
        oauth_secret = oauth_secret.encode("utf-8")

    return AES.new(key, AES.MODE_CFB, init_v).encrypt(oauth_secret)
