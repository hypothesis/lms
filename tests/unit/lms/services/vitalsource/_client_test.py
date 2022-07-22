from unittest.mock import sentinel

import pytest

from lms.services.exceptions import ExternalRequestError
from lms.services.vitalsource._client import VitalSourceClient
from tests import factories


class TestVitalSourceClient:
    def test_init(self):
        client = VitalSourceClient(api_key=sentinel.api_key)

        # pylint: disable=protected-access
        assert client._http_session.session.headers == {
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
            "GET",
            "https://api.vitalsource.com/v4/products/BOOK_ID",
            headers={"Accept": "application/json"},
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

    def test_get_table_of_contents(self, client, http_service):
        http_service.request.return_value = factories.requests.Response(
            json_data={
                "table_of_contents": [{"title": "TITLE", "cfi": "CFI", "page": "PAGE"}]
            }
        )

        book_toc = client.get_table_of_contents("BOOK_ID")

        http_service.request.assert_called_once_with(
            "GET",
            "https://api.vitalsource.com/v4/products/BOOK_ID/toc",
            headers={"Accept": "application/json"},
        )

        assert book_toc == [
            {
                "title": "TITLE",
                "cfi": "CFI",
                "page": "PAGE",
                "url": "vitalsource://book/bookID/BOOK_ID/cfi/CFI",
            }
        ]

    def test_get_table_of_contents_not_found(self, client, http_service):
        http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=404)
        )

        with pytest.raises(ExternalRequestError) as exc_info:
            client.get_table_of_contents("BOOK_ID")

        assert exc_info.value.message == "Book BOOK_ID not found"

    def test_get_table_of_contents_error(self, client, http_service):
        http_service.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=500)
        )

        with pytest.raises(ExternalRequestError):
            client.get_table_of_contents("BOOK_ID")

    @pytest.fixture
    def client(self):
        return VitalSourceClient("api_key")

    @pytest.fixture(autouse=True)
    def http_service(self, patch):
        HTTPService = patch("lms.services.vitalsource._client.HTTPService")

        return HTTPService.return_value
