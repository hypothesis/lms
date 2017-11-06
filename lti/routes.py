# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def includeme(config):
  config.add_route('welcome', '/welcome')
  config.add_route('lti_launches', '/lti_launches')
  config.add_route('module_item_configurations', '/module_item_configurations')
  config.add_route('create_module_item_configuration', '/create_module_item_configuration')

