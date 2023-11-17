import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus, unquote_plus


@dataclass
class VSBookLocation:
    """A location within a VitalSource Book."""

    book_id: str
    """Id of the book"""

    cfi: Optional[str] = None
    """Location within the book, specified as a CFI."""

    page: Optional[str] = None
    """
    Location within the book, specified as a page number.

    In most cases this will be a 1-based number, but some pages may use other
    numbering systems (eg. Roman numerals, prefixes).

    Page numbers are usually unique within a book, but this is not guaranteed.
    In the event that a page number corresponds to multiple locations, this
    VSBookLocation is taken to refer to the first such location.
    """

    @property
    def document_url(self):
        """Get our internal representation of this location."""

        url = f"vitalsource://book/bookID/{self.book_id}"

        if self.cfi:
            # CFIs are currently not escaped. This could create parsing
            # ambiguities when query params are added to the URL. If we change
            # this we need to avoid breaking existing assignments.
            url += f"/cfi/{self.cfi}"
        elif self.page:
            url += f"/page/{quote_plus(self.page)}"

        return url

    #: A regex for parsing the BOOK_ID and location parts out of one of our
    #: custom vitalsource://book/bookID/BOOK_ID/LOCATION_TYPE/LOCATION URLs.
    _DOCUMENT_URL_REGEX = re.compile(
        r"vitalsource:\/\/book\/bookID\/(?P<book_id>[^\/]*)\/(?P<loc_type>[^\/]*)\/(?P<loc>.*)"
    )

    @classmethod
    def from_document_url(cls, document_url):
        """Get a location from our internal representation."""

        match = cls._DOCUMENT_URL_REGEX.search(document_url)
        if match is None:
            raise ValueError("URL is not a valid vitalsource:// URL")

        book_id = match["book_id"]
        loc_type = match["loc_type"]
        loc = match["loc"]

        if loc_type not in ("cfi", "page"):
            raise ValueError("Invalid book location specifier")

        if loc_type == "page":
            loc = unquote_plus(loc)

        return cls(
            book_id=book_id,
            cfi=loc if loc_type == "cfi" else None,
            page=loc if loc_type == "page" else None,
        )
