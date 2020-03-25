"""Traversal resources for LTI launch views."""
import functools
import hashlib

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import Allow

from lms.resources._js_config import JSConfig
from lms.values import HUser


class LTILaunchResource:
    """Context resource for LTI launch requests."""

    __acl__ = [(Allow, "lti_user", "launch_lti_assignment")]

    def __init__(self, request):
        """Return the context resource for an LTI launch request."""
        self._request = request
        self._authority = self._request.registry.settings["h_authority"]
        self._ai_getter = self._request.find_service(name="ai_getter")

    @property
    def h_user(self):
        """
        Return the h user for the current request.

        :raise HTTPBadRequest: if any LTI params needed for generating the
          h user are missing
        """

        def username():
            """Return the h username for the current request."""
            username_hash_object = hashlib.sha1()
            username_hash_object.update(self.h_provider.encode())
            username_hash_object.update(self.h_provider_unique_id.encode())
            return username_hash_object.hexdigest()[:30]

        def display_name():
            """Return the h display name for the current request."""
            params = self._request.params

            display_name = params.get("lis_person_name_full", "").strip()

            if not display_name:
                given_name = params.get("lis_person_name_given", "").strip()
                family_name = params.get("lis_person_name_family", "").strip()

                display_name = " ".join((given_name, family_name)).strip()

            if not display_name:
                return "Anonymous"

            # The maximum length of an h display name.
            display_name_max_length = 30

            if len(display_name) <= display_name_max_length:
                return display_name

            return display_name[: display_name_max_length - 1].rstrip() + "…"

        return HUser(
            authority=self._authority, username=username(), display_name=display_name()
        )

    @property
    def h_authority_provided_id(self):
        """
        Return a unique h authority_provided_id for the request's group.

        The authority_provided_id is deterministic and is unique to the LTI
        course. Calling this function again with params representing the same
        LTI course will always return the same authority_provided_id. Calling
        this function with different params will always return a different
        authority_provided_id.

        :raise HTTPBadRequest: if an LTI param needed for generating the
            authority_provided_id is missing
        """
        # Generate the authority_provided_id based on the LTI
        # tool_consumer_instance_guid and context_id parameters.
        # These are "recommended" LTI parameters (according to the spec) that in
        # practice are provided by all of the major LMS's.
        # tool_consumer_instance_guid uniquely identifies an instance of an LMS,
        # and context_id uniquely identifies a course within an LMS. Together they
        # globally uniquely identify a course.
        hash_object = hashlib.sha1()
        hash_object.update(self._get_param("tool_consumer_instance_guid").encode())
        hash_object.update(self._get_param("context_id").encode())
        return hash_object.hexdigest()

    @property
    def h_course_group(self):
        """
        Return an h group for the current request's LTI course.

        The returned groupid is deterministic and is unique to the LTI course.
        Calling this function again with params representing the same LTI
        course will always return the same groupid. Calling this function with
        different params will always return a different groupid.

        :return: an h group for the course
        :rtype: dict

        :raise HTTPBadRequest: if an LTI param needed for generating the
            groupid is missing
        """
        groupid = f"group:{self.h_authority_provided_id}@{self._authority}"
        name = self._group_name(self._get_param("context_title").strip())

        return {
            "groupid": groupid,
            "name": name,
        }

    def h_section_group(self, tool_consumer_instance_guid, context_id, section):
        """
        Return an h group for the given Canvas course section.

        The returned groupid is deterministic and is unique to the course
        section.  Calling this function again with params representing the same
        course section will always return the same groupid. Calling this
        function with different params will always return a different groupid.

        :param tool_consumer_instance_guid: the tool_consumer_instance_guid LTI
            launch param from the Canvas instance that the section belongs to.
            This is a unique identifier for the Canvas instance
        :type tool_consumer_instance_guid: str

        :param context_id: the context_id LTI launch param from the Canvas
            course that the section belongs to. This is a unique identifier for
            the course within the Canvas instance
        :type context_id: str

        :param section: a section dict as received from the Canvas API
        :type section: dict

        :return: an h group for the section
        :rtype: dict
        """
        hash_object = hashlib.sha1()
        hash_object.update(tool_consumer_instance_guid.encode())
        hash_object.update(context_id.encode())
        hash_object.update(section["id"].encode())
        groupid = f"group:section-{hash_object.hexdigest()}@{self._authority}"

        name = section["name"].strip()

        return {"groupid": groupid, "name": self._group_name(name)}

    @property
    def h_provider(self):
        """
        Return the h "provider" string for the current request.

        :raise HTTPBadRequest: if an LTI param needed for generating the
          provider is missing
        """
        return self._get_param("tool_consumer_instance_guid")

    @property
    def h_provider_unique_id(self):
        """
        Return the h provider_unique_id for the current request.

        :raise HTTPBadRequest: if an LTI param needed for generating the
          provider unique ID is missing
        """
        return self._get_param("user_id")

    @property
    def is_canvas(self):
        """Return True if Canvas is the LMS that launched us."""
        if (
            self._request.params.get("tool_consumer_info_product_family_code")
            == "canvas"
        ):
            return True

        if "custom_canvas_course_id" in self._request.params:
            return True

        return False

    @property
    @functools.lru_cache()
    def js_config(self):
        return JSConfig(self, self._request)

    @property
    def provisioning_enabled(self):
        """
        Return True if provisioning is enabled for this request.

        Return True if the provisioning feature is enabled for the current
        request, False otherwise.

        :raise HTTPBadRequest: if there's no oauth_consumer_key in the request
          params
        """
        return self._ai_getter.provisioning_enabled(
            self._get_param("oauth_consumer_key")
        )

    @property
    def lms_url(self):
        """Return the ApplicationInstance.lms_url."""
        oauth_consumer_key = self._request.params.get("oauth_consumer_key")
        return self._ai_getter.lms_url(oauth_consumer_key)

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
        return self._request.params.get("custom_canvas_api_domain")

    def _get_param(self, param_name):
        """Return the named param from the request or raise a 400."""
        param = self._request.params.get(param_name)
        if not param:
            raise HTTPBadRequest(
                f'Required parameter "{param_name}" missing from LTI params'
            )
        return param

    @staticmethod
    def _group_name(name):
        """Return an h group name from the given course or section name."""
        # The maximum length of an h group name.
        group_name_max_length = 25

        if len(name) > group_name_max_length:
            name = name[: group_name_max_length - 1].rstrip() + "…"

        return name
