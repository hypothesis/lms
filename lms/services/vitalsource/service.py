import re
from typing import List, Optional

from lms.models import LTIParams, Course
from lms.services.vitalsource._client import VitalSourceClient
from lms.services.vitalsource.exceptions import (
    VitalSourceError,
    VitalSourceMalformedRegex,
)
from lms.services.vitalsource.model import VSBookLocation


class VitalSourceOptedOut(Exception):
    pass


class VitalSourceService:
    """A high-level interface for dealing with VitalSource."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        enabled: bool = False,
        global_client: Optional[VitalSourceClient] = None,
        customer_client: Optional[VitalSourceClient] = None,
        user_lti_param: Optional[str] = None,
        user_lti_pattern: Optional[str] = None,
        enable_licence_check: bool = True,
        enable_inclusive_access: bool = False,
        inclusive_access_vbid: Optional[str] = None,
    ):
        """
        Initialise the service.

        :param enabled: Is VitalSource enabled for the customer?
        :param global_client: Client for making generic API calls
        :param customer_client: Client for making customer specific API calls
        :param user_lti_param: Field to lookup user details for SSO
        :param user_lti_pattern: A regex to apply to the user value to get the
            id. The first capture group will be used
        :param enable_licence_check: Check users have a book licence before
            launching an SSO redirect
        """

        self._enabled = enabled
        # We can use either the customers API key (if they have one), or our
        # generic fallback key. It's better to use the customer key as it
        # ensures the books they can pick are available in their institution.
        self._metadata_client = customer_client or global_client
        # For SSO we *must* use the customers API key as the user ids only make
        # sense in the context of an institutional relationship between the uni
        # and VitalSource.
        self._sso_client = customer_client
        self._enable_licence_check = enable_licence_check
        self._user_lti_param = user_lti_param
        self._user_lti_pattern = user_lti_pattern

        self._enable_inclusive_access = enable_inclusive_access
        self._inclusive_access_vbid = inclusive_access_vbid

    @property
    def enabled(self) -> bool:
        """Check if the service has the minimum it needs to work."""

        return bool(self._enabled and self._metadata_client)

    @property
    def sso_enabled(self) -> bool:
        """Check if the service can use single sign on."""

        return bool(self.enabled and self._sso_client and self._user_lti_param)

    def get_book_info(self, book_id: str) -> dict:
        """Get details of a book."""

        return self._metadata_client.get_book_info(book_id)

    def get_table_of_contents(self, book_id: str) -> List[dict]:
        """Get the table of contents for a book."""

        return self._metadata_client.get_table_of_contents(book_id)

    @classmethod
    def get_book_reader_url(cls, document_url) -> str:
        """
        Get the public URL for VitalSource book viewer.

        :param document_url: `vitalsource://` type URL identifying the document
        """
        loc = VSBookLocation.from_document_url(document_url)

        return f"https://hypothesis.vitalsource.com/books/{loc.book_id}/cfi/{loc.cfi}"

    def get_sso_redirect(self, document_url, user_reference: str) -> str:
        """
        Get the public URL for VitalSource book viewer from our internal URL.

        That URL can be used to load VitalSource content in an iframe like we
        do with other types of content.

        :param document_url: `vitalsource://` type URL identifying the document
        :param user_reference: The user reference (you can use
            `get_user_reference()` to help you with this)
        :raises VitalSourceError: If the user has no licences for the material
            or if the service is misconfigured.
        """
        loc = VSBookLocation.from_document_url(document_url)

        # The licence check seems to unnecessarily cause problems for some
        # customers where users do have licences but the check says they
        # don't. Setting `_enable_licence_check` to `False` provides an option
        # to work around this while we work through the issue.
        if self._enable_licence_check and not self._sso_client.get_user_book_license(
            user_reference, loc.book_id
        ):
            raise VitalSourceError(error_code="vitalsource_no_book_license")

        return self._sso_client.get_sso_redirect(
            user_reference, self.get_book_reader_url(document_url)
        )

    def get_user_book_license(self, user_reference, book_id) -> Optional[dict]:
        return self._sso_client.get_user_book_license(user_reference, book_id)

    def get_user_reference(self, lti_params: LTIParams) -> Optional[str]:
        """Get the user reference from the provided LTI params."""

        value = lti_params.get(self._user_lti_param)
        if not value:
            return None

        # Some customers have wacky values in their user params which require
        # some parsing.
        if pattern := self.compile_user_lti_pattern(self._user_lti_pattern):
            match = pattern.search(value)
            return match.group(1) if match else None

        return value

    @staticmethod
    def compile_user_lti_pattern(pattern: str) -> Optional[re.Pattern]:
        """
        Compile and vet a user id pattern.

        :pattern: String format of the regex to parse
        :raise VitalSourceMalformedRegex: For any issues with the regex
        """

        if not pattern:
            return None

        try:
            compiled_pattern = re.compile(pattern)
        except re.error as err:
            raise VitalSourceMalformedRegex(str(err), pattern=pattern) from err

        if compiled_pattern.groups != 1:
            raise VitalSourceMalformedRegex(
                "The user regex must have one capture group (brackets)", pattern=pattern
            )

        return compiled_pattern

    @property
    def inclusive_access_enabled(self) -> bool:
        """Check if the current school uses the inclusive access model to access hypothesis"""

        return self._enable_inclusive_access

    def inclusive_access_student_allowed(self, lti_params, course: Course):
        user_reference = self.get_user_reference(lti_params)
        vs_course_id = vitalsource_svc.get_vs_course_id(course)
        if not vs_course_id:
            # If VS is not aware of this course it means there's no opt outs
            return
        if vitalsource_svc.get_opt_out_for_user(vs_course_id, user_reference):
            raise VitalSourceOptedOut()

    def get_vs_course_id(self, course: Course):
        if course_id := course.extra.get("vs", {}).get("course_id"):
            return course_id

        for vs_course in self._sso_client.get_courses():
            if vs_course["lms_context_id"] == course.lms_id:
                course.extra.setdefault("vs", {})
                course.extra["vs"]["course_id"] = vs_course["id"]
                return vs_course["id"]

        return None

    def get_opt_out_for_user(self, vs_course_id, user_reference):
        opt_outs = self._sso_client.get_course_opt_outs(vs_course_id)["opt_outs"]
        if not opt_outs:
            return None

        vs_user_id = None
        for user in self._sso_client.get_course_roster(vs_course_id)["users"]:
            if user["reference_id"] == user_reference:
                vs_user_id = user["id"]
                break

        if not vs_user_id:
            # We couldn't find the current user on VS lti integration.
            # There won't be any opt outs.
            return []

        for opt_out in opt_outs:
            if opt_out["sku"] != self._inclusive_access_vbid:
                continue
            if opt_out["tenant_user_id"] == vs_user_id:
                return opt_out

        return None
