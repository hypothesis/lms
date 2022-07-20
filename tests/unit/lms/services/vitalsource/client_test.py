from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any

from lms.services.exceptions import ExternalRequestError
from lms.services.vitalsource import VitalSourceService, factory
from lms.services.vitalsource.client import VitalSourceClient, VSBookLocation
from tests import factories


class TestVSBookLocation:
    TEST_CASES = [
        ("vitalsource://book/bookID/book-id/cfi//abc", "book-id", "/abc"),
        ("vitalsource://book/bookID/book-id/cfi/abc", "book-id", "abc"),
    ]

    @pytest.mark.parametrize("document_url,book_id,cfi", TEST_CASES)
    def test_from_document_url(self, document_url, book_id, cfi):
        loc = VSBookLocation.from_document_url(document_url)

        assert loc == Any.instance_of(VSBookLocation).with_attrs(
            {"book_id": book_id, "cfi": cfi}
        )

    @pytest.mark.parametrize("document_url,book_id,cfi", TEST_CASES)
    def test_document_url(self, document_url, book_id, cfi):
        loc = VSBookLocation(book_id, cfi)

        assert loc.document_url == document_url


class TestVitalSourceService:
    def test_get_launch_url(self, svc):
        document_url = "vitalsource://book/bookID/book-id/cfi//abc"

        assert (
            svc.get_launch_url(document_url)
            == "https://hypothesis.vitalsource.com/books/book-id/cfi//abc"
        )

    @pytest.mark.parametrize(
        "proxy_method,args",
        (
            ("get_book_toc", [sentinel.book_id]),
            ("get_book_info", [sentinel.book_id]),
        ),
    )
    def test_proxied_methods(self, svc, client, proxy_method, args):
        result = getattr(svc, proxy_method)(*args)

        proxied_method = getattr(client, proxy_method)
        proxied_method.assert_called_once_with(*args)
        assert result == proxied_method.return_value

    @pytest.fixture
    def client(self):
        return create_autospec(VitalSourceClient, instance=True, spec_set=True)

    @pytest.fixture
    def svc(self, client):
        return VitalSourceService(client)


class TestVitalSourceClient:
    def test_init(self):
        client = VitalSourceClient(api_key=sentinel.api_key)

        # pylint: disable=protected-access
        assert client._http_service.session.headers == {
            "X-VitalSource-API-Key": sentinel.api_key
        }

    def test_init_raises_if_launch_credentials_invalid(self):
        with pytest.raises(ValueError):
            VitalSourceClient(api_key=None)

    def test_get_book_info(self, client, http_service):
        json_data = {
            "vbid": "VBID",
            "title": "TITLE",
            "resource_links": {"cover_image": "COVER_IMAGE"},
        }
        http_service.request.return_value = factories.requests.Response(
            json_data=json_data
        )

        book_info = client.get_book_info("BOOK_ID")

        http_service.request.assert_called_once_with(
            "GET", "https://api.vitalsource.com/v4/products/BOOK_ID"
        )
        assert book_info == json_data

    def test_get_book_info_not_found(self, client, http_service):
        http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=404)
        )

        with pytest.raises(ExternalRequestError) as exc_info:
            client.get_book_info("BOOK_ID")

        assert exc_info.value.message == "Book BOOK_ID not found"

    def test_get_book_info_error(self, client, http_service):
        http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            client.get_book_info("BOOK_ID")

    def test_get_book_toc(self, client, http_service):
        http_service.request.return_value = factories.requests.Response(
            json_data={
                "table_of_contents": [{"title": "TITLE", "cfi": "CFI", "page": "PAGE"}]
            }
        )

        book_toc = client.get_book_toc("BOOK_ID")

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

    def test_get_book_toc_not_found(self, client, http_service):
        http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=404)
        )

        with pytest.raises(ExternalRequestError) as exc_info:
            client.get_book_toc("BOOK_ID")

        assert exc_info.value.message == "Book BOOK_ID not found"

    def test_get_book_toc_error(self, client, http_service):
        http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            client.get_book_toc("BOOK_ID")

    @pytest.fixture
    def client(self):
        return VitalSourceClient("api_key")

    @pytest.fixture(autouse=True)
    def http_service(self, patch):
        HTTPService = patch("lms.services.vitalsource.client.HTTPService")

        return HTTPService.return_value


class TestFactory:
    def test_it(self, pyramid_request, VitalSourceService, VitalSourceClient):
        svc = factory(sentinel.context, pyramid_request)

        VitalSourceClient.assert_called_once_with(api_key="test_vs_api_key")
        VitalSourceService.assert_called_once_with(VitalSourceClient.return_value)
        assert svc == VitalSourceService.return_value

    @pytest.fixture
    def VitalSourceService(self, patch):
        return patch("lms.services.vitalsource.client.VitalSourceService")

    @pytest.fixture
    def VitalSourceClient(self, patch):
        return patch("lms.services.vitalsource.client.VitalSourceClient")
