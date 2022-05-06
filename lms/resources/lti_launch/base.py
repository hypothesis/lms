import logging
from lms.models import LTIParams
import functools
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
        self._authority = self._request.registry.settings["h_authority"]
        self._application_instance_service = self._request.find_service(
            name="application_instance"
        )
        self._assignment_service = request.find_service(name="assignment")

    def get_or_create_course(self):
        """Get the course this LTI launch based on the request's params."""
        course_service = self._request.find_service(name="course")
        params = self._request.parsed_params

        tool_consumer_instance_guid = params["tool_consumer_instance_guid"]
        context_id = params["context_id"]

        authority_provided_id = course_service.generate_authority_provided_id(
            tool_consumer_instance_guid, context_id
        )

        legacy_course = course_service.get_or_create(authority_provided_id)
        # Capture the state here, before any other SQLA query does an implicit flush and then
        # removing legacy_course from `db.new`
        is_new_legacy_course = legacy_course in self._request.db.new

        course = course_service.upsert(
            authority_provided_id,
            context_id,
            params["context_title"],
            self._course_extra(),
            legacy_course.settings,
        )
        new_course = course.id is None

        if not is_new_legacy_course and new_course:
            LOG.warning(
                "Created course from existing legacy course. context_id: %s",
                context_id,
            )

        return legacy_course, course

    @property
    def h_group(self):
        """
        Return the h group for the current request.

        The group's name is generated from the LTI course's title and is
        usually a valid Hypothesis group name.  For example if the course's
        title is too long for a Hypothesis group name it'll be truncated. But
        this doesn't currently handle course titles that are *too short* to be
        Hypothesis group names (shorter than 3 chars) - in that case if you try
        to create a Hypothesis group using the generated name you'll get back
        an unsuccessful response from the Hypothesis API.

        The group's groupid and authority_provided_id are each deterministic
        and unique to the LTI course. Calling this function again with params
        representing the same LTI course will always return the same
        groupid and authority_provided_id. Calling this function with
        different params will always return a different groupid and
        authority_provided_id.
        """
        _, course = self.get_or_create_course()

        return course

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
    def is_canvas(self) -> bool:
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

    def sections_supported(self):
        return False

    @property
    def sections_enabled(self):
        return False

    @property
    def lti_params(self) -> LTIParams:
        """Return the requests LTI parameters."""
        return (
            LTIParams.from_v13(self._request.lti_jwt)
            if self._request.lti_jwt
            else LTIParams(self._request.params)
        )

    @property
    def is_group_launch(self):
        return False

    @property
    def groups_enabled(self):
        return False

    @property
    def _is_speedgrader(self):
        return False

    @property
    def is_legacy_speedgrader(self):
        return False

    def sync_api_config(self):
        return None

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
