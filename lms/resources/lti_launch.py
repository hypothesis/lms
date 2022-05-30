"""Traversal resources for LTI launch views."""
import functools
import logging

from lms.models import LTIParams
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
        self._authority = self._request.registry.settings["h_authority"]
        self._application_instance_service = self._request.find_service(
            name="application_instance"
        )
        self._assignment_service = request.find_service(name="assignment")

    def get_or_create_course(self):
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
    def is_legacy_speedgrader(self):
        """
        Return True if the current request is a legacy SpeedGrader launch.

        To work around a Canvas bug we add the assignment's resource_link_id as
        a query param on the LTI launch URLs that we submit to SpeedGrader (see
        https://github.com/instructure/canvas-lms/issues/1952 and
        https://github.com/hypothesis/lms/issues/3228).

        "Legacy" SpeedGrader submissions are ones from before we implemented
        this work-around, so they don't have the resource_link_id query param.
        """
        return self._is_speedgrader and not self._request.GET.get("resource_link_id")

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
    def ext_lti_assignment_id(self):
        # Canvas SpeedGrader launches don't provide ext_lti_assignment_id
        # but include it on the SpeedGrader URL we submit to canvas.
        if self._is_speedgrader and (
            ext_lti_assignment_id := self._request.GET.get("ext_lti_assignment_id")
        ):
            return ext_lti_assignment_id

        return self._request.POST.get("ext_lti_assignment_id")

    @property
    def is_canvas(self):
        """Return True if Canvas is the LMS that launched us."""
        if (
            self._request.parsed_params.get("tool_consumer_info_product_family_code")
            == "canvas"
        ):
            return True

        if "custom_canvas_course_id" in self._request.parsed_params:
            return True

        return False

    @property
    @functools.lru_cache()
    def js_config(self):
        return JSConfig(self, self._request)

    @property
    def custom_canvas_api_domain(self):
        """
        Return the domain of the Canvas API.

        FIXME: Getting this from the custom_canvas_api_domain param isn't quite
        right. This is the domain of the Canvas API which isn't the same thing
        as the domain of the Canvas website (although in practice it always
        seems to match). And of course custom_canvas_api_domain only works in
        Canvas.
        """
        return self._request.parsed_params.get("custom_canvas_api_domain")

    def canvas_sections_supported(self):
        """Return True if Canvas sections is supported for this request."""
        if not self.is_canvas:
            return False

        params = self._request.params
        if "focused_user" in params and "learner_canvas_user_id" not in params:
            # This is a legacy SpeedGrader URL, submitted to Canvas before our
            # Canvas course sections feature was released.
            return False

        try:
            application_instance = self._application_instance_service.get_current()
        except ApplicationInstanceNotFound:
            return False

        return bool(application_instance.developer_key)

    @property
    def canvas_sections_enabled(self):
        """Return True if Canvas sections is enabled for this request."""

        if not self.canvas_sections_supported():
            return False

        course = self.get_or_create_course()

        return course.settings.get("canvas", "sections_enabled")

    @property
    def canvas_groups_enabled(self):
        """Return True if Canvas groups are enabled at the school/installation level."""
        try:
            application_instance = self._application_instance_service.get_current()
        except ApplicationInstanceNotFound:
            return False

        return bool(application_instance.settings.get("canvas", "groups_enabled"))

    @property
    def blackboard_groups_enabled(self):
        """Return True if Blackboard groups are enabled at the school/installation level."""
        try:
            application_instance = self._application_instance_service.get_current()
        except ApplicationInstanceNotFound:
            return False

        return bool(application_instance.settings.get("blackboard", "groups_enabled"))

    @property
    def is_blackboard_group_launch(self):
        """Return True if the current assignment uses Blackboard groups."""
        tool_consumer_instance_guid = self._request.parsed_params[
            "tool_consumer_instance_guid"
        ]
        assignment = self._assignment_service.get(
            tool_consumer_instance_guid, self.resource_link_id
        )
        return bool(assignment and assignment.extra.get("group_set_id"))

    @property
    def canvas_is_group_launch(self):
        """Return True if the current assignment uses canvas groups."""
        try:
            int(self._request.params["group_set"])
        except (KeyError, ValueError, TypeError):
            return False
        else:
            return True

    @property
    def is_group_launch(self):
        return self.canvas_is_group_launch or self.is_blackboard_group_launch

    @property
    def lti_params(self) -> LTIParams:
        """Return the requests LTI parameters."""
        return (
            LTIParams.from_v13(self._request.lti_jwt)
            if self._request.lti_jwt
            else LTIParams(self._request.params)
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
