from unittest.mock import create_autospec, sentinel

import pytest

from lms.services.vitalsource._client import VitalSourceClient
from lms.services.vitalsource.exceptions import VitalSourceError
from lms.services.vitalsource.service import VitalSourceService


class TestVitalSourceService:
    @pytest.mark.parametrize("client", (sentinel.client, None))
    @pytest.mark.parametrize("enabled", (sentinel.client, None))
    @pytest.mark.parametrize("user_lti_param", (sentinel.user_lti_param, None))
    def test_enabled(self, client, enabled, user_lti_param):
        svc = VitalSourceService(
            client=client, enabled=enabled, user_lti_param=user_lti_param
        )

        assert svc.enabled == bool(client and enabled and user_lti_param)

    def test_get_launch_url(self, svc, client):
        result = svc.get_launch_url(
            sentinel.user_reference,
            document_url="vitalsource://book/bookID/BOOK-ID/cfi/CFI",
        )

        client.get_user_book_license.assert_called_once_with(
            sentinel.user_reference, "BOOK-ID"
        )
        client.get_sso_redirect.assert_called_once_with(
            sentinel.user_reference,
            "https://hypothesis.vitalsource.com/books/BOOK-ID/cfi/CFI",
        )
        assert result == client.get_sso_redirect.return_value

    def test_get_launch_url_with_no_book_license(self, svc, client):
        client.get_user_book_license.return_value = None

        with pytest.raises(VitalSourceError) as exc:
            svc.get_launch_url(
                sentinel.user_reference,
                document_url="vitalsource://book/bookID/BOOK-ID/cfi/CFI",
            )

        assert exc.value.error_code == "vitalsource_no_book_license"

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
        return VitalSourceService(
            client=client, enabled=True, user_lti_param=sentinel.user_lti_param
        )
