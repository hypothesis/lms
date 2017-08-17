# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging

from sqlalchemy.orm.exc import NoResultFound

from lti.models import OAuth2Credentials
from lti.models import OAuth2AccessToken


log = logging.getLogger(__name__)


# FIXME: This currently reads and writes the data to and from a JSON file, with
# the file reading and writing happening in the AuthDataService class itself.
# It should be changed to use SQLAlchemy, and to have AuthDataService
# communicate only with model classes that handle reading/writing from/to the
# db.
#
# FIXME: This currently stores one access token and refresh token pair per
# authorization server. It should be one per user account, where each
# authorization server has many user accounts.
#
# FIXME: This currently uses Canvas developer key IDs to identify authorization
# servers, but these don't look like they're globally unique. Two different
# authorization servers (i.e. two different Canvas instances) could have the
# same developer key ID. See https://github.com/hypothesis/lti/issues/14
class AuthDataService(object):
    """
    A service for getting and setting OAuth 2.0 authorization info.

    Lets you set the access token and refresh token for an authorization
    server.

    Lets you get the access token, refresh token, client secret, and URL for
    an authorization server.

    """

    def __init__(self, db):
        self._db = db

    def set_tokens(self, oauth_consumer_key, lti_token, lti_refresh_token):
        try:
            credentials = self._credentials_for(oauth_consumer_key)
        except KeyError:
            # We raise AssertionError here just to maintain compatibility with
            # the legacy API of auth_data, for now.
            raise AssertionError

        # Delete all existing access tokens for these credentials.
        for access_token in credentials.access_tokens:
            self._db.delete(access_token)

        # Save a new access and refresh token pair.
        self._db.add(OAuth2AccessToken(
            client_id=credentials.client_id,
            access_token=lti_token,
            refresh_token=lti_refresh_token,
        ))

    def get_lti_token(self, oauth_consumer_key):
        access_token = self._first_access_token_for(oauth_consumer_key)
        if access_token is None:
            return None
        return access_token.access_token

    def get_lti_refresh_token(self, oauth_consumer_key):
        access_token = self._first_access_token_for(oauth_consumer_key)
        if access_token is None:
            return None
        return access_token.refresh_token

    def get_lti_secret(self, oauth_consumer_key):
        return self._credentials_for(oauth_consumer_key).client_secret

    def get_canvas_server(self, oauth_consumer_key):
        return self._credentials_for(oauth_consumer_key).authorization_server

    def _credentials_for(self, oauth_consumer_key):
        try:
            return self._db.query(OAuth2Credentials).filter_by(
                client_id=oauth_consumer_key).one()
        except NoResultFound:
            # We raise KeyError here just to maintain compatibility with
            # the legacy API of auth_data, for now.
            raise KeyError

    def _first_access_token_for(self, oauth_consumer_key):
        credentials = self._credentials_for(oauth_consumer_key)

        if not credentials.access_tokens:
            return None

        return credentials.access_tokens[0]


def auth_data_service_factory(context, request):  # pylint: disable=unused-argument
    return AuthDataService(request.db)
