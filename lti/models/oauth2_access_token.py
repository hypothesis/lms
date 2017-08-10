# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from lti.db import BASE


class OAuth2AccessToken(BASE):
    """An access token for a user account, provided to us by an auth server."""

    __tablename__ = 'oauth2_access_token'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    client_id = sa.Column(sa.UnicodeText,
                          sa.ForeignKey('oauth2_credentials.client_id'),
                          nullable=False)
    credentials = relationship('OAuth2Credentials', back_populates='access_tokens')
    access_token = sa.Column(sa.UnicodeText, nullable=False)
    refresh_token = sa.Column(sa.UnicodeText, nullable=True)
