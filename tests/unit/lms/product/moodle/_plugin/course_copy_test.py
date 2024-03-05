from unittest.mock import sentinel

import pytest

from lms.product.moodle import MoodleCourseCopyPlugin


class TestMoodleCourseCopyPlugin:
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

    def test_find_matching_file_in_course(
        self, plugin, course_copy_files_helper, d2l_api_client
    ):
        result = plugin.find_matching_file_in_course(
            sentinel.original_file_id, sentinel.new_course_id
        )

        course_copy_files_helper.find_matching_file_in_course(
            d2l_api_client.list_files,
            "moodle_file",
            sentinel.original_file_id,
            sentinel.new_course_id,
        )

        assert (
            result == course_copy_files_helper.find_matching_file_in_course.return_value
        )

    def test_find_matching_page_in_course(
        self, plugin, course_copy_files_helper, moodle_api_client
    ):
        result = plugin.find_matching_page_in_course(
            sentinel.page_id, sentinel.course_id
        )

        course_copy_files_helper.find_matching_file_in_course.assert_called_once_with(
            moodle_api_client.list_pages,
            "moodle_page",
            sentinel.page_id,
            sentinel.course_id,
        )

        assert (
            result == course_copy_files_helper.find_matching_file_in_course.return_value
        )

    @pytest.mark.usefixtures(
        "moodle_api_client", "course_copy_files_helper", "course_copy_groups_helper"
    )
    def test_factory(self, pyramid_request):
        plugin = MoodleCourseCopyPlugin.factory(sentinel.context, pyramid_request)

        assert isinstance(plugin, MoodleCourseCopyPlugin)

    @pytest.fixture
    def plugin(self, moodle_api_client, course_copy_groups_helper):
        return MoodleCourseCopyPlugin(
            api=moodle_api_client,
            groups_helper=course_copy_groups_helper,
        )
