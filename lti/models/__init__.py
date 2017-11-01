# -*- coding: utf-8 -*-

from __future__ import unicode_literals

#from lti.models.oauth2_credentials import OAuth2Credentials
from lti.models.application_instance import ApplicationInstance

__all__ = (
    'ApplicationInstance',
)


def includeme(config):  # pylint: disable=unused-argument
    pass
