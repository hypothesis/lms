import re
from dataclasses import dataclass


@dataclass
class VSBookLocation:
    """A location within a VitalSource Book."""

    book_id: str
    """Id of the book"""

    cfi: str
    """Location within than book."""

    @property
    def document_url(self):
        """Get our internal representation of this location."""

        return f"vitalsource://book/bookID/{self.book_id}/cfi/{self.cfi}"

    #: A regex for parsing the BOOK_ID and CFI parts out of one of our custom
    #: vitalsource://book/bookID/BOOK_ID/cfi/CFI URLs.
    _DOCUMENT_URL_REGEX = re.compile(
        r"vitalsource:\/\/book\/bookID\/(?P<book_id>[^\/]*)\/cfi\/(?P<cfi>.*)"
    )

    @classmethod
    def from_document_url(cls, document_url):
        """Get a location from our internal representation."""

        return cls(**cls._DOCUMENT_URL_REGEX.search(document_url).groupdict())
