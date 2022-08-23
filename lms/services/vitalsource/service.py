from typing import List, Optional

from lms.services.vitalsource._client import VitalSourceClient
from lms.services.vitalsource.exceptions import VitalSourceError
from lms.services.vitalsource.model import VSBookLocation


class VitalSourceService:
    """A high-level interface for dealing with VitalSource."""

    user_lti_param = None
    """The LTI parameter to use to work out the LTI user."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        enabled: bool = False,
        global_client: Optional[VitalSourceClient] = None,
        customer_client: Optional[VitalSourceClient] = None,
        user_lti_param: Optional[str] = None,
        enable_licence_check: bool = True,
    ):
        """
        Initialise the service.

        :param enabled: Is VitalSource enabled for the customer?
        :param global_client: Client for making generic API calls
        :param customer_client: Client for making customer specific API calls
        :param user_lti_param: Field to lookup user details for SSO
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
        self.user_lti_param = user_lti_param

    @property
    def enabled(self) -> bool:
        """Check if the service has the minimum it needs to work."""

        return bool(self._enabled and self._metadata_client)

    @property
    def sso_enabled(self) -> bool:
        """Check if the service can use single sign on."""

        return bool(self.enabled and self._sso_client and self.user_lti_param)

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

    def get_sso_redirect(self, user_reference, document_url) -> str:
        """
        Get the public URL for VitalSource book viewer from our internal URL.

        That URL can be used to load VitalSource content in an iframe like we
        do with other types of content.

        :param user_reference: The reference of the user
        :param document_url: `vitalsource://` type URL identifying the document
        :raises VitalSourceError: If the user has no licences for the material
        """
        loc = VSBookLocation.from_document_url(document_url)

        # The licence check seems to unnecessarily cause problems for some
        # customers where users do have licences but the check says they
        # don't. Setting `_enable_licence_check` to `False` provides an option
        # to work around this while we work through the issue.
        if self._enable_licence_check and not self._sso_client.get_user_book_license(
            user_reference, loc.book_id
        ):
            raise VitalSourceError("vitalsource_no_book_license")

        return self._sso_client.get_sso_redirect(
            user_reference, self.get_book_reader_url(document_url)
        )
