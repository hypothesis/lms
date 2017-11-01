# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def includeme(config):
    config.add_route('sixty_six', '/')
    config.add_route('application_instance', '/install')
    config.add_route('lti_launches', '/lti_launches')

