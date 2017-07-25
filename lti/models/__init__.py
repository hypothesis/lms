# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from lti.models.auth_data import AuthData


def includeme(config):
    def get_auth_data(request):  # pylint: disable=unused-argument
        """Return the AuthData object."""
        return AuthData()

    config.add_request_method(get_auth_data, name='auth_data', reify=True)
