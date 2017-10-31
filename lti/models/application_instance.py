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

#    client_id = sa.Column(sa.UnicodeText,
#                          sa.ForeignKey('oauth2_credentials.client_id'),
#                          nullable=False)
#    credentials = relationship('OAuth2Credentials', back_populates='access_tokens')
#    access_token = sa.Column(sa.UnicodeText, nullable=False)
#    refresh_token = sa.Column(sa.UnicodeText, nullable=True)
