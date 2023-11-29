import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus, unquote_plus, urlparse


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

    #: A regex for parsing the book ID, location type and location out of
    #: "vitalsource://book/bookID/{book_id}/{loc_type}/{location}" URLs.
    _PATH_REGEX = re.compile(
        r"\/book\/bookID\/(?P<book_id>[^\/]*)\/(?P<loc_type>[^\/]*)\/(?P<loc>.*)"
    )

    @classmethod
    def from_document_url(cls, document_url):
        """Get a location from our internal representation."""

        parsed = urlparse(document_url)
        if parsed.scheme != "vitalsource":
            raise ValueError("URL is not a valid vitalsource:// URL")

        # `vitalsource://` URLs were not designed with URL parsing in mind
        # originally (:facepalm:), so they were structured in such a way that
        # the first part of what should have been the path becomes the host.
        path = parsed.path
        if parsed.netloc == "book":
            path = f"/{parsed.netloc}{path}"

        path_match = cls._PATH_REGEX.search(path)
        if path_match is None:
            raise ValueError("URL is not a valid vitalsource:// URL")

        book_id = path_match["book_id"]
        loc_type = path_match["loc_type"]
        loc = path_match["loc"]

        if loc_type not in ("cfi", "page"):
            raise ValueError("Invalid book location specifier")

        if loc_type == "page":
            loc = unquote_plus(loc)

        return cls(
            book_id=book_id,
            cfi=loc if loc_type == "cfi" else None,
            page=loc if loc_type == "page" else None,
        )
