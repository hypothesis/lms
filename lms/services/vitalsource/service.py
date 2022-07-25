from typing import List

from lms.services.vitalsource._client import VitalSourceClient
from lms.services.vitalsource.exceptions import VitalSourceError
from lms.services.vitalsource.model import VSBookLocation


class VitalSourceService:
    """A high-level interface for dealing with VitalSource."""

    user_lti_param = None
    """The LTI parameter to use to work out the LTI user."""

    def __init__(self, client: VitalSourceClient, enabled, user_lti_param):
        """
        Instantiate the service.

        :param client: VitalSource client for connecting to the API
        :param enabled: Are we enabled at all?
        :param user_lti_param: Which LTI parameter to read to get the user
            reference
        """
        self._client = client
        self._enabled = enabled
        self.user_lti_param = user_lti_param

    @property
    def enabled(self) -> bool:
        """Check if the service has everything it needs to work."""

        return bool(self._enabled and self._client and self.user_lti_param)

    def get_book_info(self, book_id: str) -> dict:
        """Get details of a book."""

        return self._client.get_book_info(book_id)

    def get_table_of_contents(self, book_id: str) -> List[dict]:
        """Get the table of contents for a book."""

        return self._client.get_table_of_contents(book_id)

    def get_launch_url(self, user_reference, document_url) -> str:
        """
        Get the public URL for VitalSource book viewer from our internal URL.

        That URL can be used to load VitalSource content in an iframe like we
        do with other types of content.

        :param user_reference: The reference of the user
        :param document_url: `vitalsource://` type URL identifying the document
        :raises VitalSourceError: If the user has no licences for the material
        """
        loc = VSBookLocation.from_document_url(document_url)

        if not self._client.get_user_book_license(user_reference, loc.book_id):
            raise VitalSourceError("vitalsource_no_book_license")

        url = f"https://hypothesis.vitalsource.com/books/{loc.book_id}/cfi/{loc.cfi}"
        return self._client.get_sso_redirect(user_reference, url)
