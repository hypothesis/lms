from marshmallow import EXCLUDE, Schema, fields

from lms.services.exceptions import ExternalRequestError
from lms.services.http import HTTPService
from lms.services.vitalsource.model import VSBookLocation
from lms.validation._base import RequestsResponseSchema


class VitalSourceClient:
    """
    A client for making individual calls to VitalSource API.

    See: https://developer.vitalsource.com/hc/en-us/categories/360001974433
    """

    VS_API = "https://api.vitalsource.com"

    def __init__(self, api_key: str):
        """
        Initialise a client object.

        :param api_key: Key for VitalSource API
        :raises ValueError: If credentials are invalid
        """
        if not api_key:
            raise ValueError("VitalSource credentials are missing")

        self._http_session = HTTPService()

        # Set headers in the session which will be passed with every request
        self._http_session.session.headers = {"X-VitalSource-API-Key": api_key}

    def get_book_info(self, book_id: str):
        """
        Get details of a book.

        See: https://developer.vitalsource.com/hc/en-us/articles/360010967153-GET-v4-products-vbid-Title-TOC-Metadata
        """

        try:
            response = self._json_request("GET", f"{self.VS_API}/v4/products/{book_id}")
        except ExternalRequestError as err:
            if err.status_code == 404:
                err.message = f"Book {book_id} not found"

            raise

        book_info = _BookInfoSchema(response).parse()

        return {
            "id": book_info["vbid"],
            "title": book_info["title"],
            "cover_image": book_info["resource_links"]["cover_image"],
        }

    def get_table_of_contents(self, book_id: str):
        """
        Get the table of contents for a book.

        See: https://developer.vitalsource.com/hc/en-us/articles/360010967153-GET-v4-products-vbid-Title-TOC-Metadata
        """

        try:
            response = self._json_request(
                "GET", f"{self.VS_API}/v4/products/{book_id}/toc"
            )
        except ExternalRequestError as err:
            if err.status_code == 404:
                err.message = f"Book {book_id} not found"

            raise

        toc = _BookTOCSchema(response).parse()["table_of_contents"]
        for chapter in toc:
            chapter["url"] = VSBookLocation(book_id, chapter["cfi"]).document_url

        return toc

    def _json_request(self, method, endpoint):
        # As we are using a requests Session, headers and auth etc. set in the
        # session will take effect here in addition to the values passed in.
        return self._http_session.request(
            method, endpoint, headers={"Accept": "application/json"}
        )


class _BookInfoSchema(RequestsResponseSchema):
    vbid = fields.Str(required=True)
    title = fields.Str(required=True)

    class ResourceLinks(Schema):
        class Meta:
            unknown = EXCLUDE

        cover_image = fields.Str(required=True)

    resource_links = fields.Nested(ResourceLinks, required=True)


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
