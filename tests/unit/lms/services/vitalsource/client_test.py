from unittest.mock import sentinel

import pytest

from lms.services.exceptions import ExternalRequestError
from lms.services.vitalsource import VitalSourceService, factory
from tests import factories


class TestVitalSourceService:
    def test_init(self):
        svc = VitalSourceService(api_key=sentinel.api_key)

        # pylint: disable=protected-access
        assert svc._http_service.session.headers == {
            "X-VitalSource-API-Key": sentinel.api_key
        }

    def test_init_raises_if_launch_credentials_invalid(self):
        with pytest.raises(ValueError, match="VitalSource credentials are missing"):
            VitalSourceService(api_key=None)

    @pytest.mark.parametrize(
        "url,book_id,cfi",
        [
            ("vitalsource://book/bookID/book-id/cfi//abc", "book-id", "/abc"),
            ("vitalsource://book/bookID/book-id/cfi/abc", "book-id", "abc"),
        ],
    )
    def test_parse_document_url(self, svc, url, book_id, cfi):
        assert svc.parse_document_url(url) == {
            "book_id": book_id,
            "cfi": cfi,
        }

    def test_get_launch_url(self, svc):
        document_url = "vitalsource://book/bookID/book-id/cfi//abc"

        assert (
            svc.get_launch_url(document_url)
            == "https://hypothesis.vitalsource.com/books/book-id/cfi//abc"
        )

    def test_get_book_info(self, svc, http_service):
        json_data = {
            "vbid": "VBID",
            "title": "TITLE",
            "resource_links": {"cover_image": "COVER_IMAGE"},
        }
        http_service.request.return_value = factories.requests.Response(
            json_data=json_data
        )

        book_info = svc.get_book_info("BOOK_ID")

        http_service.request.assert_called_once_with(
            "GET", "https://api.vitalsource.com/v4/products/BOOK_ID"
        )
        assert book_info == json_data

    def test_get_book_info_not_found(self, svc, http_service):
        http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=404)
        )

        with pytest.raises(ExternalRequestError) as exc_info:
            svc.get_book_info("BOOK_ID")

        assert exc_info.value.message == "Book BOOK_ID not found"

    def test_get_book_info_error(self, svc, http_service):
        http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            svc.get_book_info("BOOK_ID")

    def test_get_book_toc(self, svc, http_service):
        http_service.request.return_value = factories.requests.Response(
            json_data={
                "table_of_contents": [{"title": "TITLE", "cfi": "CFI", "page": "PAGE"}]
            }
        )

        book_toc = svc.get_book_toc("BOOK_ID")

        http_service.request.assert_called_once_with(
            "GET", "https://api.vitalsource.com/v4/products/BOOK_ID/toc"
        )

        assert book_toc == {
            "table_of_contents": [
                {
                    "title": "TITLE",
                    "cfi": "CFI",
                    "page": "PAGE",
                    "url": "vitalsource://book/bookID/BOOK_ID/cfi/CFI",
                }
            ]
        }

    def test_get_book_toc_not_found(self, svc, http_service):
        http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=404)
        )

        with pytest.raises(ExternalRequestError) as exc_info:
            svc.get_book_toc("BOOK_ID")

        assert exc_info.value.message == "Book BOOK_ID not found"

    def test_get_book_toc_error(self, svc, http_service):
        http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            svc.get_book_toc("BOOK_ID")

    @pytest.fixture
    def svc(self):
        return VitalSourceService("api_key")

    @pytest.fixture(autouse=True)
    def http_service(self, patch):
        HTTPService = patch("lms.services.vitalsource.client.HTTPService")

        return HTTPService.return_value


class TestFactory:
    def test_it(self, pyramid_request, VitalSourceService):
        svc = factory(sentinel.context, pyramid_request)

        VitalSourceService.assert_called_once_with(
            "test_vs_api_key",
        )
        assert svc == VitalSourceService.return_value

    @pytest.fixture(autouse=True)
    def VitalSourceService(self, patch):
        return patch("lms.services.vitalsource.client.VitalSourceService")
