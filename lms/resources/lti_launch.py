"""Traversal resources for LTI launch views."""
import functools

from lms.resources._js_config import JSConfig


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
        # Generate the authority_provided_id based on the LTI
        # tool_consumer_instance_guid and context_id parameters.
        # These are "recommended" LTI parameters (according to the spec) that in
        # practice are provided by all of the major LMS's.
        # tool_consumer_instance_guid uniquely identifies an instance of an LMS,
        # and context_id uniquely identifies a course within an LMS. Together they
        # globally uniquely identify a course.
        h_group_service = self._request.find_service(name="h_group_service")

        params = self._request.parsed_params

        return h_group_service.course_group(
            course_name=params["context_title"],
            tool_consumer_instance_guid=params["tool_consumer_instance_guid"],
            context_id=params["context_id"],
        )

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

        return self._request.find_service(name="ai_getter").canvas_sections_supported()

    @property
    def canvas_sections_enabled(self):
        """Return True if Canvas sections is enabled for this request."""

        if not self.canvas_sections_supported():
            return False

        course_id = self.h_group.authority_provided_id
        course = self._request.find_service(name="course").get_or_create(course_id)
        return course.settings.get("canvas", "sections_enabled")
