import logging
import secrets
from datetime import datetime
from urllib.parse import urlparse

import sqlalchemy as sa
from Cryptodome import Random
from Cryptodome.Cipher import AES
from sqlalchemy.dialects.postgresql import JSONB

from lms.db import BASE
from lms.models.application_settings import ApplicationSettings

LOG = logging.getLogger(__name__)


class ApplicationInstance(BASE):
    """Class to represent a single lms install."""

    __tablename__ = "application_instances"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    consumer_key = sa.Column(
        sa.String,
        unique=True,
        nullable=False,
        default="Hypothesis" + secrets.token_hex(16),
    )
    shared_secret = sa.Column(
        sa.String, nullable=False, default=lambda: secrets.token_hex(32)
    )
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

    #: A unique identifier for the LMS instance.
    tool_consumer_instance_guid = sa.Column(sa.UnicodeText, nullable=True)

    #: The LMS product name, e.g. "canvas" or "moodle".
    tool_consumer_info_product_family_code = sa.Column(sa.UnicodeText, nullable=True)

    #: A plain text description of the LMS instance, e.g. "University of Hypothesis"
    tool_consumer_instance_description = sa.Column(sa.UnicodeText, nullable=True)

    #: The URL of the LMS instance, e.g. "https://hypothesis.instructure.com".
    tool_consumer_instance_url = sa.Column(sa.UnicodeText, nullable=True)

    #: The name of the LMS instance, e.g. "HypothesisU".
    tool_consumer_instance_name = sa.Column(sa.UnicodeText, nullable=True)

    #: An contact email, e.g. "System.Admin@school.edu"
    tool_consumer_instance_contact_email = sa.Column(sa.UnicodeText, nullable=True)

    #: Version of the LMS, e.g. "9.1.7081"
    tool_consumer_info_version = sa.Column(sa.UnicodeText, nullable=True)

    #: This Canvas custom variable substitution $Canvas.api.domain.
    #: We request this in our config.xml file and name it "custom_canvas_api_domain":
    #:
    #: https://github.com/hypothesis/lms/blob/5394cf2bfb92cb219e177f3c0a7991add024f242/lms/templates/config.xml.jinja2#L20
    #:
    #: See https://canvas.instructure.com/doc/api/file.tools_variable_substitutions.html
    custom_canvas_api_domain = sa.Column(sa.UnicodeText, nullable=True)

    #: A list of all the OAuth2Tokens for this application instance
    #: (each token belongs to a different user of this application
    #: instance's LMS).
    access_tokens = sa.orm.relationship(
        "OAuth2Token", back_populates="application_instance"
    )

    #: A list of all the courses for this application instance.
    courses = sa.orm.relationship("LegacyCourse", back_populates="application_instance")

    #: A list of all the GroupInfo's for this application instance.
    group_infos = sa.orm.relationship(
        "GroupInfo", back_populates="application_instance"
    )

    def decrypted_developer_secret(self, aes_secret):
        if self.developer_secret is None:
            return None

        return self._cipher(aes_secret).decrypt(self.developer_secret)

    def encrypt_developer_secret(self, developer_key, developer_secret, aes_secret):
        if not developer_secret or not developer_key:
            self.developer_secret = self.developer_key = self.aes_cipher_iv = None
            return

        if self.aes_cipher_iv is None:
            self.aes_cipher_iv = Random.new().read(AES.block_size)

        self.developer_key = developer_key
        self.developer_secret = self._cipher(aes_secret).encrypt(
            developer_secret.encode("utf-8")
        )

    def _cipher(self, aes_secret):
        return AES.new(aes_secret, AES.MODE_CFB, self.aes_cipher_iv)

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

    def update_lms_data(self, params: dict):
        """
        Update all the LMS-related attributes present in `params`.

        If the current instance already has a `tool_consumer_instance_guid`
        report it on logging and don't update any of the columns.
        """

        tool_consumer_instance_guid = params.get("tool_consumer_instance_guid")
        if not tool_consumer_instance_guid:
            # guid identifies the rest of the LMS data, if not there skip any updates
            return

        if (
            self.tool_consumer_instance_guid
            and self.tool_consumer_instance_guid != tool_consumer_instance_guid
        ):
            # If we already have a LMS guid linked to the AI
            # and we found a different one report it to sentry
            LOG.exception(
                "Application Instance ID:%s launched in a different LMS install",
                self.id,
            )
            return

        self.tool_consumer_instance_guid = tool_consumer_instance_guid
        for attr in [
            "tool_consumer_info_product_family_code",
            "tool_consumer_instance_description",
            "tool_consumer_instance_url",
            "tool_consumer_instance_name",
            "tool_consumer_instance_contact_email",
            "tool_consumer_info_version",
            "custom_canvas_api_domain",
        ]:

            setattr(self, attr, params.get(attr))
