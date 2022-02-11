import logging
import secrets
from datetime import datetime
from enum import Enum
from urllib.parse import urlparse

import sqlalchemy as sa
from Cryptodome import Random
from Cryptodome.Cipher import AES
from sqlalchemy.dialects.postgresql import JSONB

from lms.db import BASE
from lms.models.application_settings import ApplicationSettings
from lms.models.exceptions import ReusedConsumerKey

LOG = logging.getLogger(__name__)


class ApplicationInstance(BASE):
    """Class to represent a single lms install."""

    class Product(str, Enum):
        BLACKBOARD = "BlackboardLearn"
        CANVAS = "canvas"
        MOODLE = "moodle"
        D2L = "desire2learn"
        BLACKBAUD = "BlackbaudK12"
        SCHOOLOGY = "schoology"
        SAKAI = "sakai"
        UNKNOWN = "unknown"

    __tablename__ = "application_instances"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    consumer_key = sa.Column(sa.Unicode, unique=True, nullable=True)
    shared_secret = sa.Column(sa.Unicode, nullable=False)
    lms_url = sa.Column(sa.Unicode(2048), nullable=False)
    requesters_email = sa.Column(sa.Unicode(2048), nullable=False)
    created = sa.Column(sa.TIMESTAMP, default=datetime.utcnow(), nullable=False)
    developer_key = sa.Column(sa.Unicode)
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

    #: A list of all the files for this application instance.
    files = sa.orm.relationship("File", back_populates="application_instance")

    # LTI1.3 platform details
    issuer = sa.Column(sa.UnicodeText, nullable=True)
    client_id = sa.Column(sa.UnicodeText, nullable=True)
    key_set_url = sa.Column(sa.UnicodeText, nullable=True)
    auth_login_url = sa.Column(sa.UnicodeText, nullable=True)
    deployment_id = sa.Column(sa.UnicodeText, nullable=True)

    # LTI1.1 rely only on consumer_key while 1.3 depend on a combination of fields
    sa.CheckConstraint(
        """(consumer_key is null
            AND issuer IS NOT NULL
            AND client_id IS NOT NULL
            AND key_set_url IS NOT NULL
            AND auth_login_url IS NOT NULL
            AND deployment_id IS NOT NULL)""",
        name="consumer_key_required_for_lti_1_1",
    ),

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
            raise ReusedConsumerKey(
                existing_guid=self.tool_consumer_instance_guid,
                new_guid=tool_consumer_instance_guid,
            )

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

    @property
    def product(self):
        try:
            product = self.Product(self.tool_consumer_info_product_family_code)
        except ValueError:
            product = self.Product.UNKNOWN

        return product

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

    @classmethod
    def build_from_lti_13_parameters(
        cls, issuer, client_id, deployment_id, auth_login_url, key_set_url
    ):

        return cls(
            issuer=issuer,
            client_id=client_id,
            deployment_id=deployment_id,
            auth_login_url=auth_login_url,
            key_set_url=key_set_url,
            shared_secret="SHOULD THIS BE NULLABLE TOO OR IS IT USED FOR NON LTI stuff?",
            lms_url=issuer,  # is it?
            requesters_email="marcos",
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
