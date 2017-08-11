# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import logging
import filelock


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

    def __init__(self, open_=None):
        self.open_ = open_ or open  # Test seam.
        self._name = 'canvas-auth.json'
        self.auth_data = {}
        self.load()

    def set_tokens(self, oauth_consumer_key, lti_token, lti_refresh_token):
        assert oauth_consumer_key in self.auth_data
        lock = filelock.FileLock("authdata.lock")
        with lock.acquire(timeout=1):
            self.auth_data[oauth_consumer_key]['lti_token'] = lti_token
            self.auth_data[oauth_consumer_key]['lti_refresh_token'] = lti_refresh_token
            self.save()

    def get_lti_token(self, oauth_consumer_key):
        return self.auth_data[oauth_consumer_key]['lti_token']

    def get_lti_refresh_token(self, oauth_consumer_key):
        return self.auth_data[oauth_consumer_key]['lti_refresh_token']

    def get_lti_secret(self, oauth_consumer_key):
        return self.auth_data[oauth_consumer_key]['secret']

    def _get_canvas_server_scheme(self, oauth_consumer_key):
        return self.auth_data[oauth_consumer_key]['canvas_server_scheme']

    def _get_canvas_server_host(self, oauth_consumer_key):
        return self.auth_data[oauth_consumer_key]['canvas_server_host']

    def _get_canvas_server_port(self, oauth_consumer_key):
        return self.auth_data[oauth_consumer_key]['canvas_server_port']

    def get_canvas_server(self, oauth_consumer_key):
        canvas_server_scheme = self._get_canvas_server_scheme(oauth_consumer_key)
        canvas_server_host = self._get_canvas_server_host(oauth_consumer_key)
        canvas_server_port = self._get_canvas_server_port(oauth_consumer_key)
        canvas_server = None
        if canvas_server_port is None:
            canvas_server = '%s://%s' % (canvas_server_scheme, canvas_server_host)
        else:
            canvas_server = '%s://%s:%s' % (canvas_server_scheme, canvas_server_host, canvas_server_port)
        return canvas_server

    def load(self):
        file_ = self.open_(self._name)
        self.auth_data = json.loads(file_.read())
        file_.close()

    def save(self):
        file_ = self.open_(self._name, 'wb')
        j = json.dumps(self.auth_data, indent=2, sort_keys=True)
        file_.write(j)
        file_.close()


def auth_data_service_factory(context, request):  # pylint: disable=unused-argument
    return AuthDataService()
