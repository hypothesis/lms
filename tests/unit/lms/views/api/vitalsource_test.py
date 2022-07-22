import pytest
from pyramid.httpexceptions import HTTPBadRequest

from lms.views.api.vitalsource import VitalSourceAPIViews


@pytest.mark.usefixtures("vitalsource_service")
class TestVitalSourceAPIViews:
    def test_book_info_returns_metadata(self, pyramid_request, vitalsource_service):
        api_book_info = {
            "vbid": "VBID",
            "title": "BOOK  TITLE",
            "resource_links": {"cover_image": "http://cover_image/url"},
        }

        vitalsource_service.get_book_info.return_value = api_book_info

        pyramid_request.matchdict["book_id"] = "BOOKSHELF-TUTORIAL"

        metadata = VitalSourceAPIViews(pyramid_request).book_info()

        assert metadata == {
            "id": api_book_info["vbid"],
            "title": api_book_info["title"],
            "cover_image": api_book_info["resource_links"]["cover_image"],
        }

    def test_table_of_contents_returns_chapter_data(
        self, pyramid_request, vitalsource_service
    ):
        vitalsource_service.get_book_toc.return_value = {
            "table_of_contents": [
                {"title": "chapter 1", "cfi": "XXXX", "page": "1"},
                ...,
            ]
        }

        pyramid_request.matchdict["book_id"] = "BOOKSHELF-TUTORIAL"
        toc = VitalSourceAPIViews(pyramid_request).table_of_contents()
        assert toc == vitalsource_service.get_book_toc.return_value["table_of_contents"]

    @pytest.mark.parametrize("method", ("book_info", "table_of_contents"))
    @pytest.mark.parametrize("invalid_book_id", ["", "lowercase", "OTHER#CHARS-OTHER"])
    def test_we_check_book_id_validity(self, pyramid_request, method, invalid_book_id):
        view = VitalSourceAPIViews(pyramid_request)

        pyramid_request.matchdict["book_id"] = invalid_book_id

        with pytest.raises(HTTPBadRequest):
            getattr(view, method)()
