# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def includeme(config):
    config.add_route('welcome', '/welcome')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('reports', '/reports')
    config.add_route('config_xml', '/config_xml')
    config.add_route('module_item_configurations', '/module_item_configurations')

    # lms routes
    config.add_route('lti_launches', '/lti_launches')
    config.add_route('content_item_selection', '/content_item_selection')

    # Assets
    config.add_route('assets', '/assets/*subpath')

    # Health check endpoint for load balancers to request.
    config.add_route('status', '/_status')
