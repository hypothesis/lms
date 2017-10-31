import sqlalchemy as sa
import secrets
from sqlalchemy.orm import relationship

from lti.db import BASE

lti_key = "MY_APP"

class ApplicationInstance(BASE):
    """TODO"""

    __tablename__ = 'application_instances'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    consumer_key = sa.Column(sa.String)
    shared_secret = sa.Column(sa.String)
    lms_url = sa.Column(sa.String(2048))

    def generate_secret():
        pass


def build_shared_secret():
    return secrets.token_hex(64)

def build_application_instance_from_lms_url(lms_url):
    return ApplicationInstance(
      consumer_key=lti_key,
      shared_secret=build_shared_secret(),
      lms_url=lms_url
    )
