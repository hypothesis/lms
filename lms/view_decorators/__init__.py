# -*- coding: utf-8 -*-

"""
Pyramid view decorators.

These are functions that can be used to decorate Pyramid view callables via the
``decorator`` argument to ``view_config``. See:

https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/viewconfig.html#view-configuration-parameters
"""

from __future__ import unicode_literals

from lms.view_decorators.h import maybe_create_user

__all__ = ("maybe_create_user",)
