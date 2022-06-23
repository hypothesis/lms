"""Traversal resources for LTI launch views."""

import logging
from functools import cached_property

from lms.models import Grouping, LTIParams
from lms.product import Product
from lms.resources._js_config import JSConfig
from lms.services import ApplicationInstanceNotFound

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
    def _is_speedgrader(self):
        return bool(self._request.GET.get("learner_canvas_user_id"))

    @property
    def resource_link_id(self):
        # Canvas SpeedGrader launches LTI apps with the wrong resource_link_id,
        # see:
        #
        # * https://github.com/instructure/canvas-lms/issues/1952
        # * https://github.com/hypothesis/lms/issues/3228
        #
        # We add the correct resource_link_id as a query param on the launch
        # URL that we submit to Canvas and use that instead of the incorrect
        # resource_link_id that Canvas puts in the request's body.
        if self._is_speedgrader and (
            resource_link_id := self._request.GET.get("resource_link_id")
        ):
            return resource_link_id

        return self.lti_params.get("resource_link_id")

    @property
    def is_canvas(self):
        """Return True if Canvas is the LMS that launched us."""
        return self._request.product.family == Product.Family.CANVAS

    @cached_property
    def js_config(self):
        return JSConfig(self, self._request)

    @property
    def sections_enabled(self):
        """Return if sections are enabled for this request."""

        if not self.is_canvas:
            # Sections are only implemented in Canvas
            return False

        params = self._request.params
        if "focused_user" in params and "learner_canvas_user_id" not in params:
            # This is a legacy SpeedGrader URL, submitted to Canvas before our
            # Canvas course sections feature was released.
            return False

        try:
            application_instance = self._request.find_service(
                name="application_instance"
            ).get_current()
        except ApplicationInstanceNotFound:
            return False

        if not bool(application_instance.developer_key):
            # We need a developer key to talk to the API
            return False

        return self.course.settings.get("canvas", "sections_enabled")

    @property
    def group_set_id(self):
        """
        Get the group set ID for group launches.

        A course can be divided in multiple "small groups" but it's possible to
        have different sets of groups for the same course.

        This ID identifies a collection of groups.
        """
        if self._request.product.family == Product.Family.CANVAS:
            # For canvas we add parameter to the launch URL as we don't store the
            # assignment during deep linking.
            try:
                return int(self._request.params.get("group_set"))
            except (TypeError, ValueError):
                return None

        elif self._request.product.family == Product.Family.BLACKBOARD:
            # In blackboard we store the configuration details in the DB
            tool_consumer_instance_guid = self._request.parsed_params[
                "tool_consumer_instance_guid"
            ]
            assignment = self._request.find_service(name="assignment").get_assignment(
                tool_consumer_instance_guid, self.resource_link_id
            )
            return assignment.extra.get("group_set_id") if assignment else None

        return None

    @property
    def grouping_type(self) -> Grouping.Type:
        """
        Return the type of grouping used in this launch.

        Grouping types describe how the course members are divided.
        If neither of the LMS grouping features are used "COURSE" is the default.
        """
        if bool(self.group_set_id):
            return Grouping.Type.GROUP

        if self.sections_enabled:
            # Sections is the default when available. Groups must take precedence
            return Grouping.Type.SECTION

        return Grouping.Type.COURSE

    @property
    def lti_params(self) -> LTIParams:
        """Return the requests LTI parameters."""
        return self._request.lti_params

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
