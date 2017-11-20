import secrets
import sqlalchemy as sa
from lms.db import BASE

# TODO we should figure out a more standard place to set this
LTI_KEY_BASE = "Hypothesis"


class ApplicationInstance(BASE):
    """Class to represent a single lms install."""

    __tablename__ = 'application_instances'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    consumer_key = sa.Column(sa.String)
    shared_secret = sa.Column(sa.String)
    lms_url = sa.Column(sa.String(2048))
    requesters_email = sa.Column(sa.String(2048))


def build_shared_secret():
    """Generate a shared secrect."""
    return secrets.token_hex(64)


def build_unique_key():
    """Use the key base to generate lms key."""
    return LTI_KEY_BASE + secrets.token_hex(16)


def build_from_lms_url(lms_url, email):
    """Intantiate ApplicationIntance with lms_url."""
    return ApplicationInstance(
        consumer_key=build_unique_key(),
        shared_secret=build_shared_secret(),
        lms_url=lms_url,
        requesters_email=email
    )
