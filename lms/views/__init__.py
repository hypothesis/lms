# -*- coding: utf-8 -*-
from lms.views.exceptions import HAPIError

__all__ = ("HAPIError",)


def includeme(config):
    config.scan(__name__)
