from unittest.mock import sentinel

import pytest

from lms.product.d2l import D2LCourseCopyPlugin


class TestD2LCourseCopyPlugin:
    def test_is_file_in_course(self, plugin, course_copy_files_helper):
        result = plugin.is_file_in_course(sentinel.course_id, sentinel.file_id)

        course_copy_files_helper.is_file_in_course.assert_called_once_with(
            sentinel.course_id, sentinel.file_id, "d2l_file"
        )

        assert result == course_copy_files_helper.is_file_in_course.return_value

    def test_find_matching_file_in_course(
        self, plugin, course_copy_files_helper, d2l_api_client
    ):
        result = plugin.find_matching_file_in_course(
            sentinel.original_file_id, sentinel.new_course_id
        )

        course_copy_files_helper.find_matching_file_in_course(
            d2l_api_client.list_files,
            "d2l_file",
            sentinel.original_file_id,
            sentinel.new_course_id,
        )

        assert (
            result == course_copy_files_helper.find_matching_file_in_course.return_value
        )

    def test_find_matching_group_set_in_course(self, plugin):
        assert not plugin.find_matching_group_set_in_course(
            sentinel.course, sentinel.group_set_id
        )

    @pytest.mark.usefixtures("d2l_api_client", "course_copy_files_helper")
    def test_factory(self, pyramid_request):
        plugin = D2LCourseCopyPlugin.factory(sentinel.context, pyramid_request)

        assert isinstance(plugin, D2LCourseCopyPlugin)

    @pytest.fixture
    def plugin(self, d2l_api_client, course_copy_files_helper):
        return D2LCourseCopyPlugin(
            api=d2l_api_client, files_helper=course_copy_files_helper
        )
