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

    @cached_property
    def course(self):
        """Get the course this LTI launch based on the request's params."""

        return self._request.find_service(name="course").upsert_course(
            context_id=self._request.parsed_params["context_id"],
            name=self._request.parsed_params["context_title"],
            extra=self._course_extra(),
        )

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

    @property
    def grouping_type(self) -> Grouping.Type:
        assignment = self._request.find_service(name="assignment").get_assignment(
            self._request.lti_params["tool_consumer_instance_guid"],
            self._request.lti_params.get("resource_link_id"),
        )
        return self._request.find_service(name="grouping").get_launch_grouping_type(
            self._request, self.course, assignment
        )

    def _course_extra(self):
        """Extra information to store for courses."""
        extra = {}

        if self.is_canvas:
            extra = {
                "canvas": {
                    "custom_canvas_course_id": self._request.parsed_params.get(
                        "custom_canvas_course_id"
                    )
                }
            }

        return extra
