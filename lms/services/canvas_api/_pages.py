from dataclasses import dataclass

from marshmallow import fields

from lms.services.file import FileService
from lms.validation import RequestsResponseSchema


@dataclass
class CanvasPage:
    id: str
    title: str
    updated_at: str

    body: str | None = None

    def canonical_url(self, lms_host, course_id):
        return f"https://{lms_host}/courses/{course_id}/pages/{self.id}"


class ListPagesSchema(RequestsResponseSchema):
    many = True

    id = fields.Integer(required=True, data_key="page_id")
    title = fields.Str(required=True)
    updated_at = fields.String(required=True)


class PagesSchema(RequestsResponseSchema):
    id = fields.Integer(required=True, data_key="page_id")
    title = fields.Str(required=True)
    updated_at = fields.String(required=True)
    body = fields.String(required=True)


class CanvasPagesClient:
    def __init__(self, client, file_service: FileService):
        self._client = client
        self._file_service = file_service

    def list(self, course_id) -> list[CanvasPage]:
        pages = self._client.send(
            "GET",
            f"courses/{course_id}/pages",
            params={"published": 1},
            schema=ListPagesSchema,
        )

        self._file_service.upsert(
            [
                {
                    "type": "canvas_page",
                    "course_id": course_id,
                    "lms_id": page["id"],
                    "name": page["title"],
                }
                for page in pages
            ]
        )

        return [
            CanvasPage(
                id=page["id"], title=page["title"], updated_at=page["updated_at"]
            )
            for page in pages
        ]

    def page(self, course_id, page_id) -> CanvasPage:
        page = self._client.send(
            "GET",
            f"courses/{course_id}/pages/{page_id}",
            schema=PagesSchema,
        )
        return CanvasPage(
            id=page["id"],
            title=page["title"],
            updated_at=page["updated_at"],
            body=page["body"],
        )
