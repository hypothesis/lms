"""Traversal resources for LTI launch views."""

import logging
from functools import cached_property

from lms.models import Grouping
from lms.product import Product
from lms.resources._js_config import JSConfig

LOG = logging.getLogger(__name__)


class LTILaunchResource:
    """
    Context resource for LTI launch requests.

    Many methods and properties of this class are only meant to be called when
    request.parsed_params holds validated params from an LTI launch request and
    might crash otherwise. So you should only call these methods after the
    request has been validated with BasicLTILaunchSchema or similar (for
    example from views that have schema=BasicLTILaunchSchema in their view
    config).
    """

    def __init__(self, request):
        """Return the context resource for an LTI launch request."""
        self._request = request

    @property
    def application_instance(self):
        """Return the current request's ApplicationInstance."""
        return self._request.find_service(name="application_instance").get_current()

    @property
    def is_canvas(self):
        """Return True if Canvas is the LMS that launched us."""
        return self._request.product.family == Product.Family.CANVAS

    @cached_property
    def js_config(self):
        return JSConfig(self, self._request)
