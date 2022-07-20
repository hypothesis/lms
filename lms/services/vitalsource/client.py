import re

from marshmallow import EXCLUDE, Schema, fields

from lms.services.exceptions import ExternalRequestError
from lms.services.http import HTTPService
from lms.validation._base import RequestsResponseSchema


class VitalSourceService:
    def __init__(self, api_key: str):
        """
        Return a new VitalSourceService.

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
            chapter["url"] = self.get_document_url(book_id, chapter["cfi"])

        return toc

    #: A regex for parsing the BOOK_ID and CFI parts out of one of our custom
    #: vitalsource://book/bookID/BOOK_ID/cfi/CFI URLs.
    _DOCUMENT_URL_REGEX = re.compile(
        r"vitalsource:\/\/book\/bookID\/(?P<book_id>[^\/]*)\/cfi\/(?P<cfi>.*)"
    )

    @classmethod
    def parse_document_url(cls, document_url):
        return cls._DOCUMENT_URL_REGEX.search(document_url).groupdict()

    @staticmethod
    def get_document_url(book_id, cfi):
        return f"vitalsource://book/bookID/{book_id}/cfi/{cfi}"

    def get_launch_url(self, document_url: str) -> str:
        """
        Return a URL to load the VitalSource book viewer at a particular book and location.

        That URL can be used to load VitalSource content in an iframe like we do with other types of content.

        Note that this method is an alternative to `get_launch_params` below.

        :param document_url: `vitalsource://` type URL identifying the document
        """
        url_params = self.parse_document_url(document_url)
        return f"https://hypothesis.vitalsource.com/books/{url_params['book_id']}/cfi/{url_params['cfi']}"

    def _get(self, endpoint):
        return self._http_service.request(
            method="GET", url=f"https://api.vitalsource.com/{endpoint}"
        )


def factory(_context, request):
    return VitalSourceService(api_key=request.registry.settings["vitalsource_api_key"])
