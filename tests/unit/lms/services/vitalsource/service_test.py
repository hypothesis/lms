from unittest.mock import create_autospec, sentinel

import pytest

from lms.services.vitalsource._client import VitalSourceClient
from lms.services.vitalsource.service import VitalSourceService


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
            ("get_book_info", [sentinel.book_id]),
            ("get_table_of_contents", [sentinel.book_id]),
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
