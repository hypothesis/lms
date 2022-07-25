from typing import List

from lms.services.vitalsource._client import VitalSourceClient
from lms.services.vitalsource.model import VSBookLocation


class VitalSourceService:
    """A high-level interface for dealing with VitalSource."""

    def __init__(self, client: VitalSourceClient, enabled):
        self._enabled = enabled
        self.client = client

    @property
    def enabled(self) -> bool:
        """Check if the service has everything it needs to work."""

        return bool(self._enabled and self.client)

    def get_book_info(self, book_id: str) -> dict:
        """Get details of a book."""

        return self.client.get_book_info(book_id)

    def get_table_of_contents(self, book_id: str) -> List[dict]:
        """Get the table of contents for a book."""

        return self.client.get_table_of_contents(book_id)

    def get_launch_url(self, document_url: str) -> str:
        """
        Get the public URL for VitalSource book viewer from our internal URL.

        That URL can be used to load VitalSource content in an iframe like we
        do with other types of content.

        :param document_url: `vitalsource://` type URL identifying the document
        """
        loc = VSBookLocation.from_document_url(document_url)

        return f"https://hypothesis.vitalsource.com/books/{loc.book_id}/cfi/{loc.cfi}"
