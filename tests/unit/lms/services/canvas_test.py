from unittest.mock import sentinel

import pytest

from lms.services import CanvasFileNotFoundInCourse, CanvasService
from lms.services.canvas import factory


class TestCanvasService:
    @pytest.mark.parametrize("check_in_course", (True, False))
    def test_public_url_for_file(self, canvas_service, check_in_course):
        canvas_service.api.list_files.return_value = [{"id": sentinel.file_id}]

        result = canvas_service.public_url_for_file(
            file_id=sentinel.file_id, check_in_course=check_in_course, course_id="*any*"
        )

        assert result == canvas_service.api.public_url.return_value
        canvas_service.api.public_url.assert_called_once_with(sentinel.file_id)

    def test_public_url_for_file_with_unsuccessful_file_check(self, canvas_service):
        canvas_service.api.list_files.return_value = []

        with pytest.raises(CanvasFileNotFoundInCourse):
            canvas_service.public_url_for_file(
                file_id=sentinel.file_id,
                course_id=sentinel.course_id,
                check_in_course=True,
            )

    @pytest.fixture
    def canvas_service(self, canvas_api_client):
        return CanvasService(canvas_api=canvas_api_client)


class TestFactory:
    def test_it(self, pyramid_request, CanvasService, canvas_api_client):
        result = factory("*any*", request=pyramid_request)

        assert result == CanvasService.return_value
        CanvasService.assert_called_once_with(canvas_api=canvas_api_client)

    @pytest.fixture
    def CanvasService(self, patch):
        return patch("lms.services.canvas.CanvasService")
