from unittest.mock import sentinel

import pytest

from lms.services import CanvasFileNotFoundInCourse, CanvasService
from lms.services.canvas import factory
from tests import factories


class TestPublicURLForFile:
    @pytest.mark.parametrize("check_in_course", (True, False))
    def test_public_url_for_file(self, canvas_service, check_in_course):
        result = canvas_service.public_url_for_file(
            file_id="2", check_in_course=check_in_course, course_id="*any*"
        )

        assert result == canvas_service.api.public_url.return_value
        canvas_service.api.public_url.assert_called_once_with("2")

    def test_public_url_for_file_with_unsuccessful_file_check(self, canvas_service):
        canvas_service.api.list_files.return_value = []

        with pytest.raises(CanvasFileNotFoundInCourse):
            canvas_service.public_url_for_file(
                file_id="2", course_id=sentinel.course_id, check_in_course=True
            )


class TestCanSeeFileInCourse:
    @pytest.mark.parametrize("file_id,expected_result", [("2", True), ("4", False)])
    def test_it(self, canvas_service, canvas_api_client, file_id, expected_result):
        result = canvas_service.can_see_file_in_course(file_id, sentinel.course_id)

        assert result == expected_result
        canvas_api_client.list_files.assert_called_once_with(sentinel.course_id)


class TestFindMatchingFileInCourse:
    def test_it_returns_the_id_if_theres_a_matching_file_in_the_course(
        self, canvas_service, canvas_api_client
    ):
        # The file dict from the Canvas API that we expect the search to match.
        matching_file_dict = canvas_api_client.list_files.return_value[1]

        file_ = factories.File(
            name=matching_file_dict["display_name"],
            size=matching_file_dict["size"],
        )

        matching_file_id = canvas_service.find_matching_file_in_course(
            sentinel.course_id, file_
        )

        canvas_api_client.list_files.assert_called_once_with(sentinel.course_id)
        assert matching_file_id == str(matching_file_dict["id"])

    def test_it_returns_None_if_theres_no_matching_file_in_the_course(
        self, canvas_service
    ):
        assert not canvas_service.find_matching_file_in_course(
            sentinel.course_id, factories.File()
        )


class TestFactory:
    def test_it(self, pyramid_request, CanvasService, canvas_api_client):
        result = factory("*any*", request=pyramid_request)

        assert result == CanvasService.return_value
        CanvasService.assert_called_once_with(canvas_api=canvas_api_client)

    @pytest.fixture
    def CanvasService(self, patch):
        return patch("lms.services.canvas.CanvasService")


@pytest.fixture
def canvas_service(canvas_api_client):
    return CanvasService(canvas_api=canvas_api_client)


@pytest.fixture
def canvas_api_client(canvas_api_client):
    canvas_api_client.list_files.return_value = [
        {"id": 1, "display_name": "File 1", "size": 1024},
        {"id": 2, "display_name": "File 2", "size": 2048},
        {"id": 3, "display_name": "File 3", "size": 3072},
    ]
    return canvas_api_client
