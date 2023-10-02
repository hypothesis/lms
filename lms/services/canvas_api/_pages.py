from dataclasses import dataclass
from typing import List, Optional

from marshmallow import fields

from lms.validation import RequestsResponseSchema


@dataclass
class CanvasPage:
    id: str
    title: str
    updated_at: str

    body: Optional[str] = None


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
    def __init__(self, client):
        self._client = client

    def list(self, course_id) -> List[CanvasPage]:
        pages = self._client.send(
            "GET",
            f"courses/{course_id}/pages",
            params={"published": 1},
            schema=ListPagesSchema,
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
