import re
from dataclasses import dataclass
from enum import Enum
from urllib.parse import parse_qs, urlparse


@dataclass
class VSBookLocation:
    """A location within a VitalSource Book."""

    class Scope(Enum):
        INSTITUTION = "institution"
        """The document is provided through an institutional relationship."""

        WILD = "wild"
        """The document is outside of an institutional relationship."""

        @classmethod
        def _missing_(cls, _value):
            return cls.WILD

    book_id: str
    """Id of the book"""

    cfi: str
    """Location within than book."""

    scope: Scope
    """Is this document scoped to an institution or the global key.

    This indicates whether the document is available with an institutional key
    and SSO, or whether this is "wild" usage where the teacher is using
    VitalSource on their own.
    """

    @property
    def document_url(self):
        """Get our internal representation of this location."""

        return f"vitalsource://book/bookID/{self.book_id}/cfi/{self.cfi}?scope={self.scope.value}"

    #: A regex for parsing the BOOK_ID and CFI parts out of the path
    _PATH_REGEX = re.compile(r"^\/bookID\/(?P<book_id>[^\/]*)\/cfi\/(?P<cfi>.*)$")

    @classmethod
    def from_document_url(cls, document_url):
        """
        Get a location from our internal representation.

        Our internal URLs look like:

            `vitalsource://book/bookID/<BOOKID>/cfi/<CFI>`
        """
        parsed = urlparse(document_url)

        # The "book" portion will be interpretted as a host
        if parsed.scheme != "vitalsource" or parsed.netloc != "book":
            # TODO! - Raise?
            return None

        match = cls._PATH_REGEX.search(parsed.path)
        if not match:
            # TODO! - Raise?
            return None

        scope = parse_qs(parsed.query).get("scope", [None])[0]

        return cls(**match.groupdict(), scope=cls.Scope(scope))
