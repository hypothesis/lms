import pytest

from lms.views.api.vitalsource import BookNotFoundError, VitalSourceAPIViews


class TestVitalSourceAPIViews:
    def test_book_info_returns_metadata(self, pyramid_request):
        pyramid_request.matchdict["book_id"] = "BOOKSHELF-TUTORIAL"

        metadata = VitalSourceAPIViews(pyramid_request).book_info()

        assert metadata == {
            "id": "BOOKSHELF-TUTORIAL",
            "title": "Bookshelf Tutorial",
            "cover_image": "https://covers.vitalbook.com/vbid/BOOKSHELF-TUTORIAL/width/480",
        }

    def test_book_info_raises_if_book_not_found(self, pyramid_request):
        pyramid_request.matchdict["book_id"] = "invalid-book-id"

        with pytest.raises(BookNotFoundError) as exc_info:
            VitalSourceAPIViews(pyramid_request).book_info()

        assert exc_info.value.explanation == "Book invalid-book-id not found"

    def test_table_of_contents_returns_chapter_data(self, pyramid_request):
        pyramid_request.matchdict["book_id"] = "BOOKSHELF-TUTORIAL"
        toc = VitalSourceAPIViews(pyramid_request).table_of_contents()
        assert len(toc) == 45

    def test_table_of_contents_raises_if_book_not_found(self, pyramid_request):
        pyramid_request.matchdict["book_id"] = "invalid-book-id"

        with pytest.raises(BookNotFoundError) as exc_info:
            VitalSourceAPIViews(pyramid_request).table_of_contents()

        assert exc_info.value.explanation == "Book invalid-book-id not found"
