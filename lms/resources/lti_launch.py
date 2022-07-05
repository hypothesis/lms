"""Traversal resources for LTI launch views."""

from functools import cached_property

from lms.models import Grouping
from lms.resources._js_config import JSConfig


class LTILaunchResource:
    """
    Context resource for LTI launch requests.

    Some methods and properties of this class are only meant to be called when
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

    @cached_property
    def course(self):
        """Get the course this LTI launch based on the request's params."""

        return self._request.find_service(name="course").upsert_course(
            context_id=self._request.parsed_params["context_id"],
            name=self._request.parsed_params["context_title"],
        )

    @property
    def grouping_type(self) -> Grouping.Type:
        """Get the type of grouping used in this launch."""

        return self._request.find_service(name="grouping").get_grouping_type()

    @cached_property
    def js_config(self):
        return JSConfig(self, self._request)
