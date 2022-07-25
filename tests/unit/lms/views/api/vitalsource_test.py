from unittest.mock import sentinel

import pytest

from lms.views.api.vitalsource import VitalSourceAPIViews


@pytest.mark.usefixtures("vitalsource_service")
class TestVitalSourceAPIViews:
    def test_book_info(self, view, pyramid_request, vitalsource_service):
        pyramid_request.matchdict["book_id"] = "BOOK-ID"

        response = view.book_info()

        vitalsource_service.get_book_info.assert_called_once_with("BOOK-ID")
        assert response == vitalsource_service.get_book_info.return_value

    def test_table_of_contents(self, view, pyramid_request, vitalsource_service):
        pyramid_request.matchdict["book_id"] = "BOOK-ID"

        response = view.table_of_contents()

        vitalsource_service.get_table_of_contents.assert_called_once_with("BOOK-ID")
        assert response == vitalsource_service.get_table_of_contents.return_value

    def test_launch_url(self, view, pyramid_request, vitalsource_service):
        pyramid_request.params["user_reference"] = sentinel.user_reference
        pyramid_request.params["document_url"] = sentinel.document_url

        response = view.launch_url()

        vitalsource_service.get_launch_url.assert_called_once_with(
            user_reference=sentinel.user_reference, document_url=sentinel.document_url
        )
        assert response == {"via_url": vitalsource_service.get_launch_url.return_value}

    @pytest.fixture
    def view(self, pyramid_request):
        return VitalSourceAPIViews(pyramid_request)
