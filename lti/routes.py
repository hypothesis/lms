# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def includeme(config):
    config.add_route('about', '/')

    config.add_route('token_callback', '/token_callback')
    config.add_route('refresh_callback', '/refresh_callback')

    config.add_route('config_xml', '/config.xml')

    config.add_route('lti_credentials', '/lti_credentials')
    config.add_route('lti_setup', '/lti_setup')
    config.add_route('lti_submit', '/lti_submit')
    config.add_route('lti_export', '/lti_export')

    config.add_route('lti_serve_pdf', '/viewer/web/{file}.pdf')
    config.add_route('catchall_pdf', '/viewer/*subpath')

    # Health check
    config.add_route('status', '/_status')
