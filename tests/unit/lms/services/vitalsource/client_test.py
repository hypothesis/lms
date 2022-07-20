from unittest import mock
from unittest.mock import sentinel

import pytest

from lms.services.exceptions import ExternalRequestError
from lms.services.vitalsource import VitalSourceService, factory
from tests import factories


class TestVitalSourceService:
    def test_init_raises_if_launch_credentials_invalid(self, http_service):
        with pytest.raises(ValueError, match="VitalSource credentials are missing"):
            VitalSourceService(http_service, api_key=None)

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

    def test_get(self, svc, http_service):
        svc.get("endpoint/path")

        http_service.get.assert_called_once_with(
            "https://api.vitalsource.com/v4/endpoint/path",
            headers={"X-VitalSource-API-Key": "api_key"},
        )

    def test_get_book_info_api(self, svc, book_info_schema):
        with mock.patch.object(VitalSourceService, "get") as get:
            book_toc = svc.get_book_info("BOOK_ID")
            get.assert_called_once_with("products/BOOK_ID")

        assert book_toc == book_info_schema.parse.return_value

    def test_get_book_info_not_found(self, svc):
        with mock.patch.object(
            VitalSourceService,
            "get",
            side_effect=ExternalRequestError(
                response=factories.requests.Response(status_code=404)
            ),
        ):
            with pytest.raises(ExternalRequestError) as exc_info:
                svc.get_book_info("BOOK_ID")

            assert exc_info.value.message == "Book BOOK_ID not found"

    def test_get_book_info_error(self, svc):
        with mock.patch.object(
            VitalSourceService,
            "get",
            side_effect=ExternalRequestError(
                response=factories.requests.Response(status_code=500)
            ),
        ):
            with pytest.raises(ExternalRequestError):
                svc.get_book_info("BOOK_ID")

    def test_get_book_toc_api(self, svc, book_toc_schema):
        with mock.patch.object(VitalSourceService, "get") as get:
            book_toc = svc.get_book_toc("BOOK_ID")
            get.assert_called_once_with("products/BOOK_ID/toc")

        assert book_toc == book_toc_schema.parse.return_value

    def test_get_book_toc_not_found(self, svc):
        with mock.patch.object(
            VitalSourceService,
            "get",
            side_effect=ExternalRequestError(
                response=factories.requests.Response(status_code=404)
            ),
        ):
            with pytest.raises(ExternalRequestError) as exc_info:
                svc.get_book_toc("BOOK_ID")

            assert exc_info.value.message == "Book BOOK_ID not found"

    def test_get_book_toc_error(self, svc):
        with mock.patch.object(
            VitalSourceService,
            "get",
            side_effect=ExternalRequestError(
                response=factories.requests.Response(status_code=500)
            ),
        ):
            with pytest.raises(ExternalRequestError):
                svc.get_book_toc("BOOK_ID")

    @pytest.fixture
    def svc(self, http_service):
        return VitalSourceService(http_service, "api_key")

    @pytest.fixture(autouse=True)
    def BookTOCSchema(self, patch):
        return patch("lms.services.vitalsource.client.BookTOCSchema")

    @pytest.fixture
    def book_toc_schema(self, BookTOCSchema):
        BookTOCSchema.return_value.context = {}
        return BookTOCSchema.return_value

    @pytest.fixture(autouse=True)
    def BookInfoSchema(self, patch):
        return patch("lms.services.vitalsource.client.BookInfoSchema")

    @pytest.fixture
    def book_info_schema(self, BookInfoSchema):
        return BookInfoSchema.return_value


class TestFactory:
    def test_it(self, http_service, pyramid_request, VitalSourceService):
        svc = factory(sentinel.context, pyramid_request)

        VitalSourceService.assert_called_once_with(
            http_service,
            "test_vs_api_key",
        )
        assert svc == VitalSourceService.return_value

    @pytest.mark.usefixtures("http_service")
    @pytest.mark.parametrize(
        "name_of_missing_envvar",
        [
            "vitalsource_api_key",
        ],
    )
    def test_it_raises_if_an_envvar_is_missing(
        self, pyramid_request, name_of_missing_envvar
    ):
        del pyramid_request.registry.settings[name_of_missing_envvar]

        with pytest.raises(KeyError):
            factory(sentinel.context, pyramid_request)

    @pytest.fixture(autouse=True)
    def VitalSourceService(self, patch):
        return patch("lms.services.vitalsource.client.VitalSourceService")
