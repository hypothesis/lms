import pytest
from h_matchers import Any

from lms.services.vitalsource import VSBookLocation


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
