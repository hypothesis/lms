from unittest.mock import call, sentinel

import pytest

from lms.product.canvas import CanvasCourseCopyPlugin
from lms.services.exceptions import ExternalRequestError, OAuth2TokenError
from tests import factories


class TestCanvasCourseCopyPlugin:
    def test_find_matching_group_set_in_course(self, plugin, course_copy_groups_helper):
        result = plugin.find_matching_group_set_in_course(
            sentinel.course, sentinel.group_set_id
        )

        course_copy_groups_helper.find_matching_group_set_in_course.assert_called_once_with(
            sentinel.course, sentinel.group_set_id
        )

        assert (
            result
            == course_copy_groups_helper.find_matching_group_set_in_course.return_value
        )

    def test_is_file_in_course(self, plugin, course_copy_files_helper):
        result = plugin.is_file_in_course(sentinel.course_id, sentinel.file_id)

        course_copy_files_helper.is_file_in_course.assert_called_once_with(
            sentinel.course_id, sentinel.file_id, "canvas_file"
        )

        assert result == course_copy_files_helper.is_file_in_course.return_value

    def test_find_matching_file_raises_OAuth2TokenError(
        self, plugin, canvas_api_client
    ):
        canvas_api_client.list_files.side_effect = OAuth2TokenError

        with pytest.raises(OAuth2TokenError):
            plugin.find_matching_file_in_course(sentinel.course_id, [sentinel.file_id])

    @pytest.mark.parametrize("raising", [True, False])
    def test_find_matching_file_in_course_returns_the_matching_file_id(
        self, plugin, canvas_api_client, file_service, raising
    ):
        if raising:
            canvas_api_client.list_files.side_effect = ExternalRequestError

        file_service.get.return_value = factories.File()

        matching_file_id = plugin.find_matching_file_in_course(
            sentinel.course_id, [sentinel.file_id]
        )

        file_service.get.assert_called_once_with(sentinel.file_id, type_="canvas_file")
        canvas_api_client.list_files.assert_called_once_with(sentinel.course_id)
        file_service.find_copied_file.assert_called_once_with(
            sentinel.course_id, file_service.get.return_value
        )
        assert matching_file_id == file_service.find_copied_file.return_value.lms_id

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
        file_service.find_copied_file.side_effect = [
            None,
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
        assert matching_file_id == matching_file.lms_id

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
        file_service.find_copied_file.return_value = None

        assert not plugin.find_matching_file_in_course(
            sentinel.course_id, [sentinel.file_id]
        )

    def test_find_matching_page_in_course(
        self, plugin, course_copy_files_helper, canvas_api_client
    ):
        result = plugin.find_matching_page_in_course(
            sentinel.page_id, sentinel.course_id
        )

        course_copy_files_helper.find_matching_file_in_course.assert_called_once_with(
            canvas_api_client.pages.list,
            "canvas_page",
            sentinel.page_id,
            sentinel.course_id,
        )

        assert (
            result == course_copy_files_helper.find_matching_file_in_course.return_value
        )

    @pytest.mark.usefixtures(
        "canvas_api_client",
        "file_service",
        "course_copy_files_helper",
        "course_copy_groups_helper",
    )
    def test_factory(self, pyramid_request):
        plugin = CanvasCourseCopyPlugin.factory(sentinel.context, pyramid_request)

        assert isinstance(plugin, CanvasCourseCopyPlugin)

    @pytest.fixture
    def plugin(
        self,
        canvas_api_client,
        file_service,
        course_copy_files_helper,
        course_copy_groups_helper,
    ):
        return CanvasCourseCopyPlugin(
            api=canvas_api_client,
            file_service=file_service,
            files_helper=course_copy_files_helper,
            groups_helper=course_copy_groups_helper,
        )
