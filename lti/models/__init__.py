# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from lti.models.oauth2_credentials import OAuth2Credentials
from lti.models.oauth2_access_token import OAuth2AccessToken


__all__ = (
    'OAuth2Credentials',
    'OAuth2AccessToken',
)


def includeme(config):  # pylint: disable=unused-argument
    pass
