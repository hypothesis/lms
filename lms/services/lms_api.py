from typing import Literal, Protocol, Self, TypedDict


class LMSDocument(TypedDict):
    """Represents a document or folder in an LMS's file storage."""

    type: Literal["File", "Folder"]

    id: str
    lms_id: str
    display_name: str
    updated_at: str

    children: list[Self]


class LMSAPI(Protocol):
    def list_files(self, course_id: int) -> list[LMSDocument]:  # pragma: no cover
        ...
