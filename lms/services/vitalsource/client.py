from marshmallow import EXCLUDE, Schema, fields

from lms.services.exceptions import ExternalRequestError
from lms.services.http import HTTPService
from lms.services.vitalsource.model import VSBookLocation
from lms.validation._base import RequestsResponseSchema


class VitalSourceClient:
    def __init__(self, api_key: str):
        """
        Initialise a client object.

        :param api_key: Key for VitalSource API
        :raises ValueError: If credentials are invalid
        """
        if not api_key:
            raise ValueError("VitalSource credentials are missing")

        self._http_service = HTTPService()
        self._http_service.session.headers = {"X-VitalSource-API-Key": api_key}

    class _BookInfoSchema(RequestsResponseSchema):
        vbid = fields.Str(required=True)
        title = fields.Str(required=True)

        class ResourceLinks(Schema):
            class Meta:
                unknown = EXCLUDE

            cover_image = fields.Str(required=True)

        resource_links = fields.Nested(ResourceLinks, required=True)

    def get_book_info(self, book_id: str):
        try:
            response = self._get(f"v4/products/{book_id}")
        except ExternalRequestError as err:
            if err.status_code == 404:
                err.message = f"Book {book_id} not found"

            raise

        return self._BookInfoSchema(response).parse()

    class _BookTOCSchema(RequestsResponseSchema):
        class Chapter(Schema):
            class Meta:
                unknown = EXCLUDE

            title = fields.Str(required=True)
            cfi = fields.Str(required=True)
            page = fields.Str(required=True)

            url = fields.Str(required=False)
            """vitalsource:// like url identifying the book and chapter"""

        table_of_contents = fields.List(fields.Nested(Chapter), required=True)

    def get_book_toc(self, book_id: str):
        try:
            response = self._get(f"v4/products/{book_id}/toc")
        except ExternalRequestError as err:
            if err.status_code == 404:
                err.message = f"Book {book_id} not found"

            raise

        toc = self._BookTOCSchema(response).parse()
        for chapter in toc["table_of_contents"]:
            chapter["url"] = VSBookLocation(book_id, chapter["cfi"]).document_url

        return toc

    def _get(self, endpoint):
        return self._http_service.request(
            method="GET", url=f"https://api.vitalsource.com/{endpoint}"
        )
