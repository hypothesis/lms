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

    def _documents_for_storage(  # pylint:disable=too-many-arguments
        self,
        course_id,
        files: list[LMSDocument],
        folder_type: str,
        document_type: str,
        parent_id=None,
    ):
        """Reshape a list of LMSDocument for storage in the File table."""
        for file in files:
            yield {
                "type": folder_type if file["type"] == "Folder" else document_type,
                "course_id": course_id,
                "lms_id": file["lms_id"],
                "name": file["display_name"],
                "parent_lms_id": parent_id,
            }

            yield from self._documents_for_storage(
                course_id,
                file.get("children", []),
                folder_type,
                document_type,
                file["id"],
            )
