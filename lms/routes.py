# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def includeme(config):
    config.add_route('welcome', '/welcome')
    config.add_route('config_xml', '/config_xml')
    config.add_route('module_item_configurations', '/module_item_configurations')
    config.add_route('test_api', '/test_api')

    # lms routes
    config.add_route('lti_launches', '/lti_launches')
    config.add_route('content_item_selection', '/content_item_selection')
