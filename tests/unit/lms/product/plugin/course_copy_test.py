from unittest.mock import Mock, create_autospec, sentinel

import pytest

from lms.product.plugin.course_copy import CourseCopyFilesHelper
from lms.services.exceptions import ExternalRequestError, OAuth2TokenError
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
            sentinel.course_id, sentinel.file_id, sentinel.type
        )

        file_service.get.assert_called_once_with(sentinel.file_id, sentinel.type)
        assert is_in_course == expected

    @pytest.mark.parametrize("raising", [True, False])
    def test_find_matching_file_in_course(
        self, helper, file_service, raising, store_new_course_files
    ):
        if raising:
            store_new_course_files.side_effect = ExternalRequestError

        file_service.get.return_value = factories.File()
        file_service.find_copied_file.return_value = factories.File()

        new_file = helper.find_matching_file_in_course(
            store_new_course_files,
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

    def test_find_matching_file_raises_OAuth2TokenError(
        self, helper, store_new_course_files
    ):
        store_new_course_files.side_effect = OAuth2TokenError

        with pytest.raises(OAuth2TokenError):
            helper.find_matching_file_in_course(
                store_new_course_files,
                sentinel.file_type,
                sentinel.original_file_id,
                sentinel.new_course_id,
            )

    def test_find_matching_file_in_course_no_existing_file(self, helper, file_service):
        store_new_course_files = Mock()
        file_service.get.return_value = factories.File()
        file_service.find_copied_file.return_value = None

        assert not helper.find_matching_file_in_course(
            store_new_course_files,
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
            sentinel.file_type,
            sentinel.original_file_id,
            sentinel.new_course_id,
        )

        store_new_course_files.assert_called_once_with(sentinel.new_course_id)
        file_service.get.assert_called_once_with(
            sentinel.original_file_id, type_=sentinel.file_type
        )

    @pytest.mark.usefixtures("file_service")
    def test_factory(self, pyramid_request):
        plugin = CourseCopyFilesHelper.factory(sentinel.context, pyramid_request)

        assert isinstance(plugin, CourseCopyFilesHelper)

    @pytest.fixture
    def helper(self, file_service):
        return CourseCopyFilesHelper(file_service=file_service)

    @pytest.fixture
    def store_new_course_files(self):
        return create_autospec(lambda _: None)  # pragma: nocover
