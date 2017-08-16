# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from lti.db import BASE


class OAuth2Credentials(BASE):
    """OAuth 2.0 client credentials provided to us by an authorization server."""

    __tablename__ = 'oauth2_credentials'

    #: The OAuth 2.0 client_id.
    client_id = sa.Column(sa.UnicodeText, primary_key=True)

    #: The OAuth 2.0 client_secret.
    client_secret = sa.Column(sa.UnicodeText, nullable=False)

    #: The OAuth 2.0 authorization server that these credentials came from.
    authorization_server = sa.Column(sa.UnicodeText, nullable=False)

    #: A list of all the access tokens that we currently have from these
    #: credentials.
    access_tokens = relationship('OAuth2AccessToken',
                                 cascade='all, delete, delete-orphan')
