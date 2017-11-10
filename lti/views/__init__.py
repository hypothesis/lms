# -*- coding: utf-8 -*-
from lti.views.application_instances import create_application_instance
from lti.views.config import config_xml
from lti.views.content_item_selection import content_item_selection
from lti.views.lti_launches import lti_launches
from lti.views.module_item_configurations import create_module_item_configuration


__all__ = (
    'create_application_instance',
    'config_xml',
    'content_item_selection',
    'lti_launches',
    'create_module_item_configuration'
)


def includeme(config):
    config.scan(__name__)
