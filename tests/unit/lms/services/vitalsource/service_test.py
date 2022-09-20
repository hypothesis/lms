import re
from unittest.mock import create_autospec, sentinel

import pytest
from _pytest.mark import param

from lms.models import LTIParams
from lms.services.vitalsource._client import VitalSourceClient
from lms.services.vitalsource.exceptions import VitalSourceMalformedRegex
from lms.services.vitalsource.service import VitalSourceService


class TestVitalSourceService:
    @pytest.mark.parametrize("global_client", (sentinel.global_client, None))
    @pytest.mark.parametrize("customer_client", (sentinel.customer_client, None))
    @pytest.mark.parametrize("enabled", (sentinel.client, None))
    def test_enabled(self, enabled, global_client, customer_client):
        svc = VitalSourceService(
            enabled=enabled,
            global_client=global_client,
            customer_client=customer_client,
        )

        assert svc.enabled == bool(enabled and (global_client or customer_client))

    @pytest.mark.parametrize("enabled", (sentinel.client, None))
    @pytest.mark.parametrize("customer_client", (sentinel.customer_client, None))
    @pytest.mark.parametrize("user_lti_param", (sentinel.user_lti_param, None))
    def test_sso_enabled(self, enabled, customer_client, user_lti_param):
        svc = VitalSourceService(
            enabled=enabled,
            customer_client=customer_client,
            user_lti_param=user_lti_param,
        )

        assert svc.sso_enabled == bool(enabled and customer_client and user_lti_param)

    def test_get_book_reader_url(self, svc):
        url = svc.get_book_reader_url("vitalsource://book/bookID/BOOK-ID/cfi/CFI")

        assert url == "https://hypothesis.vitalsource.com/books/BOOK-ID/cfi/CFI"

    def test_get_sso_redirect(self, svc, customer_client):
        result = svc.get_sso_redirect(
            document_url="vitalsource://book/bookID/BOOK-ID/cfi/CFI",
            user_reference=sentinel.user_reference,
        )

        customer_client.get_sso_redirect.assert_called_once_with(
            sentinel.user_reference,
            "https://hypothesis.vitalsource.com/books/BOOK-ID/cfi/CFI",
        )
        assert result == customer_client.get_sso_redirect.return_value

    @pytest.mark.parametrize(
        "value,pattern,user_reference",
        (
            ("user_id_12345", None, "user_id_12345"),
            ("user_id_12345", "^user_id_(.*)$", "12345"),
            ("user_id_12345", "NOT_(A)_MATCH", None),
            (None, None, None),
        ),
    )
    def test_get_user_reference(self, value, pattern, user_reference):
        svc = VitalSourceService(user_lti_param="user_param", user_lti_pattern=pattern)

        result = svc.get_user_reference(LTIParams({"user_param": value}))

        assert result == user_reference

    @pytest.mark.parametrize(
        "proxy_method,args",
        (
            ("get_book_info", [sentinel.book_id]),
            ("get_table_of_contents", [sentinel.book_id]),
        ),
    )
    @pytest.mark.parametrize("customer_client_present", (True, False))
    def test_metadata_methods(
        self,
        global_client,
        customer_client,
        customer_client_present,
        proxy_method,
        args,
    ):
        svc = VitalSourceService(
            enabled=True,
            global_client=global_client,
            customer_client=customer_client if customer_client_present else None,
        )

        result = getattr(svc, proxy_method)(*args)

        proxied_method = getattr(
            customer_client if customer_client_present else global_client, proxy_method
        )
        proxied_method.assert_called_once_with(*args)
        assert result == proxied_method.return_value

    def test_compile_user_lti_pattern(self):
        pattern = VitalSourceService.compile_user_lti_pattern("a(.*)c")

        assert isinstance(pattern, re.Pattern)
        assert pattern.search("abc").group(1) == "b"

    @pytest.mark.parametrize(
        "bad_pattern",
        (
            param("[", id="malformed"),
            param(".*", id="no capture group"),
            param(".*(a)(b)", id="too many capture groups"),
        ),
    )
    def test_compile_user_lti_pattern_with_invalid_patterns(self, bad_pattern):
        with pytest.raises(VitalSourceMalformedRegex):
            VitalSourceService.compile_user_lti_pattern(bad_pattern)

    @pytest.fixture
    def global_client(self):
        return create_autospec(VitalSourceClient, instance=True, spec_set=True)

    @pytest.fixture
    def customer_client(self):
        return create_autospec(VitalSourceClient, instance=True, spec_set=True)

    @pytest.fixture
    def svc(self, global_client, customer_client):
        return VitalSourceService(
            enabled=True,
            global_client=global_client,
            customer_client=customer_client,
            user_lti_param=sentinel.user_lti_param,
        )
