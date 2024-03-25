from typing import Literal, NotRequired, Protocol, TypedDict


class APICallInfo(TypedDict):
    path: str
    authUrl: NotRequired[str]


class LMSDocument(TypedDict):
    """Represents a document or folder in an LMS's file storage."""

    type: Literal["File", "Folder"]
    mime_type: NotRequired[Literal["text/html", "application/pdf", "video"]]

    id: str
    """ID of the document in our sytem. Often in the form schema://DETAILS/"""

    lms_id: str
    """ID of the document in the LMS itself."""

    display_name: str
    updated_at: str

    children: NotRequired[list["LMSDocument"]]
    """Children of the current folder."""

    contents: NotRequired[APICallInfo]
    """API call to use to fetch contents of a folder."""


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
