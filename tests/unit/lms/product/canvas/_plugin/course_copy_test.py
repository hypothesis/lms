from unittest.mock import call, sentinel

import pytest

from lms.product.canvas import CanvasCourseCopyPlugin
from tests import factories


class TestCanvasCourseCopyPlugin:
    def test_find_matching_group_set_in_course(self, plugin):
        assert not plugin.find_matching_group_set_in_course(
            sentinel.course, sentinel.group_set_id
        )

    def test_is_file_in_course(self, plugin, course_copy_files_helper):
        result = plugin.is_file_in_course(sentinel.course_id, sentinel.file_id)

        course_copy_files_helper.is_file_in_course.assert_called_once_with(
            sentinel.course_id, sentinel.file_id, "canvas_file"
        )

        assert result == course_copy_files_helper.is_file_in_course.return_value

    def test_find_matching_file_in_course_returns_the_matching_file_id(
        self, plugin, canvas_api_client, file_service
    ):
        file_service.get.return_value = factories.File()
        canvas_api_client.list_files.return_value = [
            {"id": 1, "display_name": "File 1", "size": 1024},
            {
                "id": sentinel.matching_file_id,
                "display_name": file_service.get.return_value.name,
                "size": file_service.get.return_value.size,
            },
        ]

        matching_file_id = plugin.find_matching_file_in_course(
            sentinel.course_id, [sentinel.file_id]
        )

        file_service.get.assert_called_once_with(sentinel.file_id, type_="canvas_file")
        canvas_api_client.list_files.assert_called_once_with(sentinel.course_id)
        assert matching_file_id == str(sentinel.matching_file_id)

    def test_find_matching_file_in_course_with_multiple_file_ids(
        self, plugin, canvas_api_client, file_service
    ):
        matching_file = factories.File()
        file_service.get.side_effect = [
            # The first file_id isn't found in the DB.
            None,
            # The second file_id is in the DB but not found in the course.
            factories.File(),
            # The third file_id *will* be found in the course.
            matching_file,
        ]
        canvas_api_client.list_files.return_value = [
            {
                "id": sentinel.matching_file_id,
                "display_name": matching_file.name,
                "size": matching_file.size,
            },
        ]

        matching_file_id = plugin.find_matching_file_in_course(
            sentinel.course_id,
            [sentinel.file_id_1, sentinel.file_id_2, sentinel.file_id_3],
        )

        # It looked up each file_id in the DB in turn.
        assert file_service.get.call_args_list == [
            call(sentinel.file_id_1, type_="canvas_file"),
            call(sentinel.file_id_2, type_="canvas_file"),
            call(sentinel.file_id_3, type_="canvas_file"),
        ]
        assert matching_file_id == str(sentinel.matching_file_id)

    def test_find_matching_file_in_course_returns_None_if_theres_no_file_in_the_db(
        self, plugin, file_service
    ):
        file_service.get.return_value = None

        assert not plugin.find_matching_file_in_course(
            sentinel.course_id, [sentinel.file_id]
        )

    def test_find_matching_file_in_course_returns_None_if_theres_no_match(
        self, plugin, file_service
    ):
        file_service.get.return_value = factories.File(name="foo")

        assert not plugin.find_matching_file_in_course(
            sentinel.course_id, [sentinel.file_id]
        )

    def test_find_matching_file_in_course_doesnt_return_the_same_file(
        self, plugin, canvas_api_client, file_service
    ):
        # If the response from the Canvas API contains a "matching" file dict
        # that happens to be the *same* file as the one we're searching for (it
        # has the same id) find_matching_file_in_course() should not return
        # the same file_id as it was asked to search for a match for.
        matching_file_dict = canvas_api_client.list_files.return_value[1]
        file_service.get.return_value = factories.File(
            lms_id=str(matching_file_dict["id"]),
            name=matching_file_dict["display_name"],
            size=matching_file_dict["size"],
        )

        assert not plugin.find_matching_file_in_course(
            sentinel.course_id, [sentinel.file_id]
        )

    @pytest.mark.usefixtures(
        "canvas_api_client", "file_service", "course_copy_files_helper"
    )
    def test_factory(self, pyramid_request):
        plugin = CanvasCourseCopyPlugin.factory(sentinel.context, pyramid_request)

        assert isinstance(plugin, CanvasCourseCopyPlugin)

    @pytest.fixture
    def plugin(self, canvas_api_client, file_service, course_copy_files_helper):
        return CanvasCourseCopyPlugin(
            api=canvas_api_client,
            file_service=file_service,
            files_helper=course_copy_files_helper,
        )
