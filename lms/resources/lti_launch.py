"""Traversal resources for LTI launch views."""

import logging
from functools import cached_property

from lms.resources._js_config import JSConfig

LOG = logging.getLogger(__name__)


class LTILaunchResource:
    """Context resource for LTI launch requests."""

    def __init__(self, request):
        """Return the context resource for an LTI launch request."""
        self._request = request

    @property
    def application_instance(self):
        """Return the current request's ApplicationInstance."""
        return self._request.find_service(name="application_instance").get_current()

    @cached_property
    def js_config(self):
        return JSConfig(self, self._request)
