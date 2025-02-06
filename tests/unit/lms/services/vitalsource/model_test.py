from urllib.parse import urlparse

import pytest
from h_matchers import Any

from lms.services.vitalsource import VSBookLocation


class TestVSBookLocation:
    TEST_CASES = [  # noqa: RUF012
        # Book ID + CFI
        ("vitalsource://book/bookID/book-id/cfi//abc", "book-id", "/abc", None),
        ("vitalsource://book/bookID/book-id/cfi/abc", "book-id", "abc", None),
        # Book ID + Page number
        ("vitalsource://book/bookID/book-id/page/23", "book-id", None, "23"),
        ("vitalsource://book/bookID/book-id/page/iv", "book-id", None, "iv"),
        ("vitalsource://book/bookID/book-id/page/A+B", "book-id", None, "A B"),
        # Book ID with page number and end page
        (
            "vitalsource://book/bookID/book-id/page/20?end_page=10",
            "book-id",
            None,
            "20",
        ),
        # Book ID with CFI and end CFI
        (
            "vitalsource://book/bookID/book-id/cfi//1/2?end_cfi=/2/3",
            "book-id",
            "/1/2",
            None,
        ),
    ]

    @pytest.mark.parametrize("document_url,book_id,cfi,page", TEST_CASES)
    def test_from_document_url(self, document_url, book_id, cfi, page):
        loc = VSBookLocation.from_document_url(document_url)

        assert loc == Any.instance_of(VSBookLocation).with_attrs(
            {"book_id": book_id, "cfi": cfi, "page": page}
        )

    @pytest.mark.parametrize(
        "document_url,expected",
        [
            # Wrong scheme
            ("https://example.org", "URL is not a valid vitalsource:// URL"),
            # Wrong path (first component)
            (
                "vitalsource://not-a-book/bookID/a-book/page/123",
                "URL is not a valid vitalsource:// URL",
            ),
            # Wrong path (other component)
            (
                "vitalsource://book/not-a-bookID/a-book/page/123",
                "URL is not a valid vitalsource:// URL",
            ),
            # Wrong location type ("pageindex" instead of "page")
            (
                "vitalsource://book/bookID/a-book/pageindex/123",
                "Invalid book location specifier",
            ),
        ],
    )
    def test_from_document_url_invalid(self, document_url, expected):
        with pytest.raises(ValueError) as exc_info:  # noqa: PT011
            VSBookLocation.from_document_url(document_url)
        assert str(exc_info.value) == expected

    @pytest.mark.parametrize("document_url,book_id,cfi,page", TEST_CASES)
    def test_document_url(self, document_url, book_id, cfi, page):
        loc = VSBookLocation(book_id, cfi, page)

        def strip_query(url: str) -> str:
            parsed = urlparse(url)
            return parsed._replace(query="").geturl()

        assert loc.document_url == strip_query(document_url)
