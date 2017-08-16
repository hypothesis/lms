# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sqlalchemy as sa

from lti.db import BASE


class OAuth2UnvalidatedCredentials(BASE):
    """
    Unvalidated OAuth 2.0 client credentials.

    This table contains unvalidated OAuth 2.0 client credentials submitted by
    users using the ``/lti_credentials`` form. These must be manually validated
    and then copied into the oauth2_credentials table.

    """

    __tablename__ = 'oauth2_unvalidated_credentials'

    # In the real OAuth2Credentials table the ``client_id`` must be unique and
    # is used as the primary key. In this unvalidated table we add a simple
    # auto incrementing integer primary key, so that the same ``client_id`` can
    # be submitted multiple times.
    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    # Users can _either_ submit a client_id and client_secret or just an
    # access_token.
    client_id = sa.Column(sa.UnicodeText)
    client_secret = sa.Column(sa.UnicodeText)
    authorization_server = sa.Column(sa.UnicodeText)
    email_address = sa.Column(sa.UnicodeText())
