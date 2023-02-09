from unittest.mock import sentinel

import pytest

from lms.product.blackboard import BlackboardCourseCopyPlugin


class TestBlackboardCourseCopyPlugin:
    def test_is_file_in_course(self, plugin, course_copy_files_helper):
        result = plugin.is_file_in_course(sentinel.course_id, sentinel.file_id)

        course_copy_files_helper.is_file_in_course.assert_called_once_with(
            sentinel.course_id, sentinel.file_id, "blackboard_file"
        )

        assert result == course_copy_files_helper.is_file_in_course.return_value

    def test_find_matching_file_in_course(
        self, plugin, course_copy_files_helper, blackboard_api_client
    ):
        result = plugin.find_matching_file_in_course(
            sentinel.original_file_id, sentinel.new_course_id
        )

        course_copy_files_helper.find_matching_file_in_course(
            blackboard_api_client.list_all_files,
            "blackboard_file",
            sentinel.original_file_id,
            sentinel.new_course_id,
        )

        assert (
            result == course_copy_files_helper.find_matching_file_in_course.return_value
        )

    @pytest.mark.usefixtures("blackboard_api_client", "course_copy_files_helper")
    def test_factory(self, pyramid_request):
        plugin = BlackboardCourseCopyPlugin.factory(sentinel.context, pyramid_request)

        assert isinstance(plugin, BlackboardCourseCopyPlugin)

    @pytest.fixture
    def plugin(self, blackboard_api_client, course_copy_files_helper):
        return BlackboardCourseCopyPlugin(
            api=blackboard_api_client, files_helper=course_copy_files_helper
        )
