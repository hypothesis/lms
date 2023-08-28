import re
from dataclasses import dataclass
from typing import Optional

DOCUMENT_URL_REGEXES = {
    # canvas://file/course/COURSE_ID/file_id/FILE_ID
    "canvas": re.compile(
        r"canvas:\/\/file\/course\/(?P<course_id>[^\/]*)\/file_id\/(?P<file_id>[^\/]*)"
    ),
    # blackboard://content-resource/<file_id>/ URLs
    "blackboard": re.compile(r"blackboard:\/\/content-resource\/(?P<file_id>[^\/]*)\/"),
    # d2l://file/course/COURSE_ID/file_id/FILE_ID.
    "d2l": re.compile(
        r"d2l:\/\/file\/course\/(?P<course_id>[^\/]*)\/file_id\/(?P<file_id>[^\/]*)\/"
    ),
}


@dataclass
class DocumentURLParts:
    file_id: str
    course_id: Optional[str] = None


class DocumentService:
    def get_document_url_parts(self, url: str) -> Optional[DocumentURLParts]:
        """Return the parts of a given document_url."""
        for regexp in DOCUMENT_URL_REGEXES.values():
            if match := regexp.search(url):
                match_dict = match.groupdict()
                return DocumentURLParts(
                    course_id=match_dict.get("course_id"), file_id=match_dict["file_id"]
                )

        return None


def factory(_context, _request) -> DocumentService:
    return DocumentService()
