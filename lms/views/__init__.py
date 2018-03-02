# -*- coding: utf-8 -*-
from lms.views.application_instances import create_application_instance
from lms.views.config import config_xml
from lms.views.content_item_selection import content_item_selection
from lms.views.lti_launches import lti_launches
from lms.views.module_item_configurations import create_module_item_configuration
from lms.views.canvas_proxy import canvas_proxy
from lms.views.reports import list_application_instances

__all__ = (
    'create_application_instance',
    'config_xml',
    'content_item_selection',
    'lti_launches',
    'create_module_item_configuration',
    'canvas_proxy',
    'list_application_instances'
)


def includeme(config):
    config.scan(__name__)
