import re
from dataclasses import dataclass
from typing import Optional
from enum import Enum, unique
from lms.services.file import FileService


@unique
class DocumentType(str, Enum):
    BLACKBOARD_FILE = "blackboard_file"
    D2L_FILE = "d2l_file"
    CANVAS_FILE = "canvas_file"


DOCUMENT_URL_REGEXES = {
    # canvas://file/course/COURSE_ID/file_id/FILE_ID
    DocumentType.CANVAS_FILE: re.compile(
        r"canvas:\/\/file\/course\/(?P<course_id>[^\/]*)\/file_id\/(?P<file_id>[^\/]*)"
    ),
    # blackboard://content-resource/<file_id>/ URLs
    DocumentType.BLACKBOARD_FILE: re.compile(
        r"blackboard:\/\/content-resource\/(?P<file_id>[^\/]*)\/"
    ),
    # d2l://file/course/COURSE_ID/file_id/FILE_ID.
    DocumentType.D2L_FILE: re.compile(
        r"d2l:\/\/file\/course\/(?P<course_id>[^\/]*)\/file_id\/(?P<file_id>[^\/]*)\/"
    ),
}


@dataclass
class DocumentURLParts:
    type_: str
    file_id: str
    course_id: Optional[str] = None


@dataclass
class Document:
    lms_url: str
    filename: Optional[str] = None


class DocumentService:
    def __init__(self, file_service):
        self._file_service = file_service

    def get_document_url_parts(self, url: str) -> Optional[DocumentURLParts]:
        """Return the parts of a given document_url."""
        for type_, regexp in DOCUMENT_URL_REGEXES.items():
            if match := regexp.search(url):
                match_dict = match.groupdict()
                return DocumentURLParts(
                    type_=type_,
                    course_id=match_dict.get("course_id"),
                    file_id=match_dict["file_id"],
                )

        return None

    def get_document_from_assignment(self, assignment) -> Document:
        """Get a Document based on the assignment configuration."""
        document = Document(lms_url=assignment.document_url)
        if document_parts := self.get_document_url_parts(assignment.document_url):
            if file := self._file_service.get(
                document_parts.file_id,
                type_=document_parts.type_,
                course_id=document_parts.course_id,
            ):
                document.filename = file.name

        return document


def factory(_context, request) -> DocumentService:
    return DocumentService(file_service=request.find_service(name="file"))
