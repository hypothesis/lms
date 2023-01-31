from unittest.mock import create_autospec, sentinel

import pytest

from lms.product.d2l import D2LCourseCopyPlugin
from lms.product.plugin.course_copy import CourseCopyFilesHelper


class TestD2LCourseCopyPlugin:
    def test_is_file_in_course(self, plugin, helper, file_service):
        result = plugin.is_file_in_course(sentinel.course_id, sentinel.file_id)

        helper.is_file_in_course.assert_called_once_with(
            file_service, sentinel.course_id, sentinel.file_id, "d2l_file"
        )

        assert result == helper.is_file_in_course.return_value

    def test_find_matching_file_in_course(
        self, plugin, helper, file_service, d2l_api_client
    ):
        result = plugin.find_matching_file_in_course(
            sentinel.original_file_id, sentinel.new_course_id
        )

        helper.find_matching_file_in_course(
            d2l_api_client.list_files,
            file_service,
            "d2l_file",
            sentinel.original_file_id,
            sentinel.new_course_id,
        )

        assert result == helper.find_matching_file_in_course.return_value

    def test_get_mapped_file_id(self, plugin, helper):
        result = plugin.get_mapped_file_id(sentinel.course, sentinel.file_id)

        helper.get_mapped_file_id.assert_called_once_with(
            sentinel.course, sentinel.file_id
        )

        assert result == helper.get_mapped_file_id.return_value

    def test_set_mapped_file_id(self, plugin, helper):
        plugin.set_mapped_file_id(
            sentinel.course, sentinel.old_file_id, sentinel.new_file_id
        )

        helper.set_mapped_file_id.assert_called_once_with(
            sentinel.course, sentinel.old_file_id, sentinel.new_file_id
        )

    @pytest.mark.usefixtures("d2l_api_client", "file_service")
    def test_factory(self, pyramid_request):
        plugin = D2LCourseCopyPlugin.factory(sentinel.context, pyramid_request)

        assert isinstance(plugin, D2LCourseCopyPlugin)

    @pytest.fixture
    def helper(self):
        return create_autospec(CourseCopyFilesHelper, spec_set=True, instance=True)

    @pytest.fixture
    def plugin(self, d2l_api_client, file_service, helper):
        return D2LCourseCopyPlugin(
            api=d2l_api_client, file_service=file_service, files_helper=helper
        )
