# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from lms.models.application_instance import ApplicationInstance
from lms.models.module_item_configuration import ModuleItemConfiguration

__all__ = (
    'ApplicationInstance',
    'ModuleItemConfiguration'
)


def includeme(config):  # pylint: disable=unused-argument
    pass
