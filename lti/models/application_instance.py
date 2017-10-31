import sqlalchemy as sa
from sqlalchemy.orm import relationship

from lti.db import BASE


class ApplicationInstance(BASE):
    """TODO"""

    __tablename__ = 'application_instances'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    consumer_key = sa.Column(sa.String)
    shared_secret = sa.Column(sa.String)
    lms_url = sa.Column(sa.String(2048))
