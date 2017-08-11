# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def includeme(config):
    config.register_service_factory('.auth_data.auth_data_service_factory',
                                    name='auth_data')
