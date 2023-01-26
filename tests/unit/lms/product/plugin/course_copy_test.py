from unittest.mock import Mock, create_autospec, sentinel

import pytest

from lms.product.plugin.course_copy import CourseCopyFilesHelper
from lms.services.exceptions import ExternalRequestError
from tests import factories


class TestCourseCopyFilesHelper:
    @pytest.mark.parametrize(
        "file,expected",
        [
            (factories.File.build(course_id=sentinel.course_id), True),
            (None, False),
            (factories.File.build(course_id=sentinel.other_course), False),
        ],
    )
    def test_is_file_in_course(self, file_service, helper, file, expected):
        file_service.get.return_value = file

        is_in_course = helper.is_file_in_course(
            file_service, sentinel.course_id, sentinel.file_id, sentinel.type
        )

        file_service.get.assert_called_once_with(sentinel.file_id, sentinel.type)
        assert is_in_course == expected

    @pytest.mark.parametrize("raising", [True, False])
    def test_find_matching_file_in_course(self, helper, file_service, raising):
        store_new_course_files = create_autospec(
            lambda new_course_id: None  # pragma: nocover
        )
        if raising:
            store_new_course_files.side_effect = ExternalRequestError

        file_service.get.return_value = factories.File()
        file_service.find_copied_file.return_value = factories.File()

        new_file = helper.find_matching_file_in_course(
            store_new_course_files,
            file_service,
            sentinel.file_type,
            sentinel.original_file_id,
            sentinel.new_course_id,
        )

        store_new_course_files.assert_called_once_with(sentinel.new_course_id)
        file_service.get.assert_called_once_with(
            sentinel.original_file_id, type_=sentinel.file_type
        )
        file_service.find_copied_file.assert_called_once_with(
            sentinel.new_course_id, file_service.get.return_value
        )

        assert new_file

    def test_find_matching_file_in_course_no_existing_file(self, helper, file_service):
        store_new_course_files = Mock()
        file_service.get.return_value = factories.File()
        file_service.find_copied_file.return_value = None

        assert not helper.find_matching_file_in_course(
            store_new_course_files,
            file_service,
            sentinel.file_type,
            sentinel.original_file_id,
            sentinel.new_course_id,
        )

        store_new_course_files.assert_called_once_with(sentinel.new_course_id)
        file_service.get.assert_called_once_with(
            sentinel.original_file_id, type_=sentinel.file_type
        )
        file_service.find_copied_file.assert_called_once_with(
            sentinel.new_course_id, file_service.get.return_value
        )

    def test_find_matching_file_in_course_no_copied_file(self, helper, file_service):
        store_new_course_files = Mock()
        file_service.get.return_value = None

        assert not helper.find_matching_file_in_course(
            store_new_course_files,
            file_service,
            sentinel.file_type,
            sentinel.original_file_id,
            sentinel.new_course_id,
        )

        store_new_course_files.assert_called_once_with(sentinel.new_course_id)
        file_service.get.assert_called_once_with(
            sentinel.original_file_id, type_=sentinel.file_type
        )

    def test_get_mapped_file_empty_extra(self, helper):
        course = factories.Course(extra={})

        assert not helper.get_mapped_file_id(course, "ID")

    def test_get_mapped_file_empty_mapping(self, helper):
        course = factories.Course(extra={"course_copy_file_mappings": {}})

        assert not helper.get_mapped_file_id(course, "ID")

    def test_get_mapped_file(self, helper):
        course = factories.Course(
            extra={"course_copy_file_mappings": {"ID": "OTHER_ID"}}
        )

        assert helper.get_mapped_file_id(course, "ID") == "OTHER_ID"

    def test_set_mapped_file_id(self, helper):
        course = factories.Course(extra={})

        helper.set_mapped_file_id(course, "OLD", "NEW")

        assert course.extra["course_copy_file_mappings"]["OLD"] == "NEW"

    @pytest.fixture
    def helper(self):
        return CourseCopyFilesHelper()
