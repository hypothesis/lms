import pytest
from h_matchers import Any

from lms.services.vitalsource import VSBookLocation


class TestVSBookLocation:
    TEST_CASES = [
        # Book ID + CFI
        ("vitalsource://book/bookID/book-id/cfi//abc", "book-id", "/abc", None),
        ("vitalsource://book/bookID/book-id/cfi/abc", "book-id", "abc", None),
        # Book ID + Page number
        ("vitalsource://book/bookID/book-id/page/23", "book-id", None, "23"),
        ("vitalsource://book/bookID/book-id/page/iv", "book-id", None, "iv"),
        ("vitalsource://book/bookID/book-id/page/A+B", "book-id", None, "A B"),
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
            ("https://example.org", "URL is not a valid vitalsource:// URL"),
            (
                "vitalsource://book/bookID/a-book/pageindex/123",
                "Invalid book location specifier",
            ),
        ],
    )
    def test_from_document_url_invalid(self, document_url, expected):
        with pytest.raises(ValueError) as exc_info:
            VSBookLocation.from_document_url(document_url)
        assert str(exc_info.value) == expected

    @pytest.mark.parametrize("document_url,book_id,cfi,page", TEST_CASES)
    def test_document_url(self, document_url, book_id, cfi, page):
        loc = VSBookLocation(book_id, cfi, page)

        assert loc.document_url == document_url
