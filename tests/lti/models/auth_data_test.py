# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from lti.models.auth_data import AuthData


class TestAuthData(object):

    """Unit tests for the AuthData class."""

    def test_it_doesnt_crash_when_you_instantiate_it(self):
        auth_data = AuthData()
