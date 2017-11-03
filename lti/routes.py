# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def includeme(config):
  config.add_route('welcome', '/welcome')
  config.add_route('lti_launches', '/lti_launches')

