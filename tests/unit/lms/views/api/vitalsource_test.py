import pytest
from pyramid.httpexceptions import HTTPBadRequest

from lms.views.api.vitalsource import VitalSourceAPIViews


@pytest.mark.usefixtures("vitalsource_service")
class TestVitalSourceAPIViews:
    def test_book_info(self, pyramid_request, vitalsource_service):
        pyramid_request.matchdict["book_id"] = "BOOK-ID"

        response = VitalSourceAPIViews(pyramid_request).book_info()

        vitalsource_service.get_book_info.assert_called_once_with("BOOK-ID")
        assert response == vitalsource_service.get_book_info.return_value

    def test_table_of_contents(self, pyramid_request, vitalsource_service):
        pyramid_request.matchdict["book_id"] = "BOOK-ID"

        response = VitalSourceAPIViews(pyramid_request).table_of_contents()

        vitalsource_service.get_table_of_contents.assert_called_once_with("BOOK-ID")
        assert response == vitalsource_service.get_table_of_contents.return_value

    @pytest.mark.parametrize("method", ("book_info", "table_of_contents"))
    @pytest.mark.parametrize("invalid_book_id", ["", "lowercase", "OTHER#CHARS-OTHER"])
    def test_we_check_book_id_validity(self, pyramid_request, method, invalid_book_id):
        view = VitalSourceAPIViews(pyramid_request)

        pyramid_request.matchdict["book_id"] = invalid_book_id

        with pytest.raises(HTTPBadRequest):
            getattr(view, method)()
