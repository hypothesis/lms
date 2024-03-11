import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from lms.models import LTIParams
from lms.services.vitalsource._client import VitalSourceClient
from lms.services.vitalsource.exceptions import VitalSourceMalformedRegex
from lms.services.vitalsource.model import VSBookLocation


class VitalSourceService:
    """A high-level interface for dealing with VitalSource."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        enabled: bool = False,
        global_client: VitalSourceClient | None = None,
        customer_client: VitalSourceClient | None = None,
        user_lti_param: str | None = None,
        user_lti_pattern: str | None = None,
    ):
        """
        Initialise the service.

        :param enabled: Is VitalSource enabled for the customer?
        :param global_client: Client for making generic API calls
        :param customer_client: Client for making customer specific API calls
        :param user_lti_param: Field to lookup user details for SSO
        :param user_lti_pattern: A regex to apply to the user value to get the
            id. The first capture group will be used
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
        self._user_lti_param = user_lti_param
        self._user_lti_pattern = user_lti_pattern

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

    def get_table_of_contents(self, book_id: str) -> list[dict]:
        """Get the table of contents for a book."""

        return self._metadata_client.get_table_of_contents(book_id)

    def get_document_url(
        self,
        book_id: str,
        page: str | None = None,
        cfi: str | None = None,
        end_page: str | None = None,
        end_cfi: str | None = None,
    ) -> str:
        """
        Generate the document URL for an assignment.

        :param book_id: VitalSource book ID (aka. "vbid")
        :param page: Start location as a page number
        :param cfi: Start location as a CFI
        :param end_page: End location as a page number
        :param end_cfi: End location as a CFI
        """
        url = VSBookLocation(book_id, cfi=cfi, page=page).document_url

        url = urlparse(url)
        params = parse_qs(url.query)
        if end_page:
            params["end_page"] = end_page
        if end_cfi:
            params["end_cfi"] = end_cfi
        url = url._replace(query=urlencode(params, doseq=True))

        return urlunparse(url)

    @classmethod
    def get_client_focus_config(cls, document_url: str) -> dict | None:
        """
        Get the content range for an assignment from a `vitalsource://` URL.

        Returns a dict suitable for merging into the Hypothesis client's
        "focus" configuration, or `None` if the URL doesn't specify a range.
        """
        loc = VSBookLocation.from_document_url(document_url)
        parsed_url = urlparse(document_url)
        params = parse_qs(parsed_url.query)

        if loc.cfi and "end_cfi" in params:
            end_cfi = params["end_cfi"][-1]
            return {
                "cfi": {
                    "range": f"{loc.cfi}-{end_cfi}",
                    # We currently use a generic label to describe the selected
                    # content. It would be nicer to present the chapter name.
                    "label": "selected chapters",
                }
            }

        if loc.page and "end_page" in params:
            end_page = params["end_page"][-1]
            return {
                "pages": f"{loc.page}-{end_page}",
            }

        return None

    @classmethod
    def get_book_reader_url(cls, document_url) -> str:
        """
        Get the public URL for VitalSource book viewer.

        :param document_url: `vitalsource://` type URL identifying the document
        """
        loc = VSBookLocation.from_document_url(document_url)
        prefix = f"https://hypothesis.vitalsource.com/books/{loc.book_id}"

        if loc.cfi:
            return f"{prefix}/cfi/{loc.cfi}"
        if loc.page:
            return f"{prefix}/page/{loc.page}"
        return prefix  # pragma: nocover

    def get_sso_redirect(self, document_url, user_reference: str) -> str:
        """
        Get the public URL for VitalSource book viewer from our internal URL.

        That URL can be used to load VitalSource content in an iframe like we
        do with other types of content.

        :param document_url: `vitalsource://` type URL identifying the document
        :param user_reference: The user reference (you can use
            `get_user_reference()` to help you with this)
        """
        return self._sso_client.get_sso_redirect(
            user_reference, self.get_book_reader_url(document_url)
        )

    def get_user_reference(self, lti_params: LTIParams) -> str | None:
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
    def compile_user_lti_pattern(pattern: str) -> re.Pattern | None:
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
