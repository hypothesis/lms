import re
from unittest.mock import create_autospec, sentinel

import pytest
from _pytest.mark import param

from lms.error_code import ErrorCode
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

    @pytest.mark.parametrize(
        "doc_url,reader_url",
        [
            (
                "vitalsource://book/bookID/BOOK-ID/cfi/CFI",
                "https://hypothesis.vitalsource.com/books/BOOK-ID/cfi/CFI",
            ),
            (
                "vitalsource://book/bookID/BOOK-ID/page/42",
                "https://hypothesis.vitalsource.com/books/BOOK-ID/page/42",
            ),
        ],
    )
    def test_get_book_reader_url(self, svc, doc_url, reader_url):
        url = svc.get_book_reader_url(doc_url)
        assert url == reader_url

    @pytest.mark.parametrize(
        "doc_url,expected_config",
        [
            ("vitalsource://book/bookID/BOOK-ID/cfi/CFI", None),
            ("vitalsource://book/bookID/BOOK-ID/page/42", None),
            (
                "vitalsource://book/bookID/BOOK-ID/page/42?end_page=50",
                {"pages": "42-50"},
            ),
            (
                "vitalsource://book/bookID/BOOK-ID/cfi/CFI?end_cfi=END_CFI",
                {"cfi": {"range": "CFI-END_CFI", "label": "selected chapters"}},
            ),
        ],
    )
    def test_get_client_focus_config(self, svc, doc_url, expected_config):
        config = svc.get_client_focus_config(doc_url)
        assert config == expected_config

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

    def test_check_h_license_disabled(self, svc, pyramid_request):
        svc._student_pay_enabled = False  # noqa: SLF001

        assert not svc.check_h_license(
            pyramid_request.lti_user, pyramid_request.lti_params, sentinel.assignment
        )

    @pytest.mark.parametrize(
        "user_fixture,code",
        [
            (
                "user_is_instructor",
                ErrorCode.VITALSOURCE_STUDENT_PAY_LICENSE_LAUNCH_INSTRUCTOR,
            ),
            ("user_is_learner", ErrorCode.VITALSOURCE_STUDENT_PAY_LICENSE_LAUNCH),
        ],
    )
    def test_check_h_license_course_launch(
        self, request, svc, pyramid_request, user_fixture, code
    ):
        svc._student_pay_enabled = True  # noqa: SLF001
        _ = request.getfixturevalue(user_fixture)

        assert (
            svc.check_h_license(
                pyramid_request.lti_user, pyramid_request.lti_params, None
            )
            == code
        )

    @pytest.mark.usefixtures("user_is_learner")
    def test_check_h_license_failure(self, svc, pyramid_request, customer_client):
        svc._student_pay_enabled = True  # noqa: SLF001
        customer_client.get_user_book_license.return_value = None

        assert (
            svc.check_h_license(
                pyramid_request.lti_user,
                pyramid_request.lti_params,
                sentinel.assignment,
            )
            == ErrorCode.VITALSOURCE_STUDENT_PAY_NO_LICENSE
        )

        customer_client.get_user_book_license.assert_called_once_with(
            svc.get_user_reference(pyramid_request.lti_params), svc.H_SKU
        )

    @pytest.mark.usefixtures("user_is_learner")
    def test_check_h_license_success(self, svc, pyramid_request, customer_client):
        svc._student_pay_enabled = True  # noqa: SLF001
        customer_client.get_user_book_license.return_value = sentinel.license

        assert not (
            svc.check_h_license(
                pyramid_request.lti_user,
                pyramid_request.lti_params,
                sentinel.assignment,
            )
        )

    @pytest.mark.usefixtures("user_is_instructor")
    def test_check_h_license_no_license_check_for_instructors(
        self, svc, pyramid_request, customer_client
    ):
        svc._student_pay_enabled = True  # noqa: SLF001

        assert not (
            svc.check_h_license(
                pyramid_request.lti_user,
                pyramid_request.lti_params,
                sentinel.assignment,
            )
        )
        customer_client.get_user_book_license.assert_not_called()

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

    @pytest.mark.parametrize(
        "page,cfi,end_page,end_cfi,expected",
        [
            # Book ID only
            (
                None,
                None,
                None,
                None,
                "vitalsource://book/bookID/some_book",
            ),
            # Book ID + start CFI
            (
                None,
                "/1/2",
                None,
                None,
                "vitalsource://book/bookID/some_book/cfi//1/2",
            ),
            # Book ID + start page
            (
                "23",
                None,
                None,
                None,
                "vitalsource://book/bookID/some_book/page/23",
            ),
            # Book ID + start and end page
            (
                "23",
                None,
                "46",
                None,
                "vitalsource://book/bookID/some_book/page/23?end_page=46",
            ),
            # Book ID + start and end CFI
            (
                None,
                "/1/2",
                None,
                "/3/4",
                "vitalsource://book/bookID/some_book/cfi//1/2?end_cfi=%2F3%2F4",
            ),
        ],
    )
    def test_get_document_url(self, svc, page, cfi, end_page, end_cfi, expected):
        url = svc.get_document_url(
            book_id="some_book", page=page, cfi=cfi, end_page=end_page, end_cfi=end_cfi
        )
        assert url == expected

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
