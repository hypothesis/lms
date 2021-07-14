from functools import partial
from unittest.mock import call, sentinel

import pytest

from lms.services import (
    CanvasAPIPermissionError,
    CanvasFileNotFoundInCourse,
    CanvasService,
)
from lms.services.canvas import CanvasFileFinder, factory
from tests import factories


class TestPublicURLForFile:
    @pytest.mark.parametrize("check_in_course", [True, False])
    def test_the_happy_path(
        self,
        canvas_api_client,
        canvas_file_finder,
        check_in_course,
        file_service,
        public_url_for_file,
        CanvasFileFinder,
    ):
        url = public_url_for_file(sentinel.file_id, check_in_course=check_in_course)

        CanvasFileFinder.assert_called_once_with(canvas_api_client, file_service)
        if check_in_course:
            canvas_file_finder.assert_file_in_course.assert_called_once_with(
                sentinel.course_id, sentinel.file_id
            )
        else:
            canvas_file_finder.assert_file_in_course.assert_not_called()
        canvas_api_client.public_url.assert_called_once_with(sentinel.file_id)
        assert url == canvas_api_client.public_url.return_value

    @pytest.mark.usefixtures("with_mapped_file_id")
    def test_if_theres_a_mapped_file_id_it_uses_it(
        self, canvas_api_client, canvas_file_finder, public_url_for_file
    ):
        url = public_url_for_file(sentinel.file_id, check_in_course=True)

        canvas_file_finder.assert_file_in_course.assert_called_once_with(
            sentinel.course_id, sentinel.mapped_file_id
        )
        canvas_api_client.public_url.assert_called_once_with(sentinel.mapped_file_id)
        assert url == canvas_api_client.public_url.return_value

    @pytest.mark.usefixtures("with_mapped_file_id")
    def test_if_the_file_isnt_in_the_course_it_finds_a_matching_file_instead(
        self,
        canvas_api_client,
        canvas_file_finder,
        module_item_configuration,
        public_url_for_file,
    ):
        canvas_file_finder.assert_file_in_course.side_effect = (
            CanvasFileNotFoundInCourse(sentinel.file_id)
        )
        canvas_file_finder.find_matching_file_in_course.return_value = (
            sentinel.found_file_id
        )

        url = public_url_for_file(sentinel.file_id, check_in_course=True)

        canvas_file_finder.find_matching_file_in_course.assert_called_once_with(
            sentinel.course_id, {sentinel.file_id, sentinel.mapped_file_id}
        )
        assert (
            module_item_configuration.get_canvas_mapped_file_id(sentinel.file_id)
            == sentinel.found_file_id
        )
        canvas_api_client.public_url.assert_called_once_with(sentinel.found_file_id)
        assert url == canvas_api_client.public_url.return_value

    @pytest.mark.usefixtures("with_mapped_file_id")
    def test_if_the_file_isnt_in_the_course_and_theres_no_matching_file_it_raises(
        self, canvas_file_finder, public_url_for_file
    ):
        canvas_file_finder.assert_file_in_course.side_effect = (
            CanvasFileNotFoundInCourse(sentinel.file_id)
        )
        canvas_file_finder.find_matching_file_in_course.return_value = None

        with pytest.raises(CanvasFileNotFoundInCourse):
            public_url_for_file(sentinel.file_id, check_in_course=True)

    @pytest.mark.usefixtures("with_mapped_file_id")
    def test_if_theres_a_permissions_error_it_finds_a_matching_file_instead(
        self,
        canvas_api_client,
        canvas_file_finder,
        module_item_configuration,
        public_url_for_file,
    ):
        canvas_api_client.public_url.side_effect = [
            CanvasAPIPermissionError,
            sentinel.url,
        ]
        canvas_file_finder.find_matching_file_in_course.return_value = (
            sentinel.found_file_id
        )

        url = public_url_for_file(sentinel.file_id)

        canvas_file_finder.find_matching_file_in_course.assert_called_once_with(
            sentinel.course_id, {sentinel.file_id, sentinel.mapped_file_id}
        )
        assert (
            module_item_configuration.get_canvas_mapped_file_id(sentinel.file_id)
            == sentinel.found_file_id
        )
        assert canvas_api_client.public_url.call_args_list == [
            call(sentinel.mapped_file_id),
            call(sentinel.found_file_id),
        ]
        assert url == sentinel.url

    @pytest.mark.usefixtures("with_mapped_file_id")
    def test_if_theres_a_permissions_error_and_theres_no_matching_file_it_raises(
        self, canvas_api_client, canvas_file_finder, public_url_for_file
    ):
        canvas_api_client.public_url.side_effect = CanvasAPIPermissionError
        canvas_file_finder.find_matching_file_in_course.return_value = None

        with pytest.raises(CanvasAPIPermissionError):
            public_url_for_file(sentinel.file_id)

    def test_it_doesnt_save_a_mapped_file_id_if_getting_that_files_public_url_fails(
        self,
        canvas_api_client,
        canvas_file_finder,
        module_item_configuration,
        public_url_for_file,
    ):
        canvas_api_client.public_url.side_effect = CanvasAPIPermissionError
        canvas_file_finder.find_matching_file_in_course.return_value = (
            sentinel.found_file_id
        )

        with pytest.raises(CanvasAPIPermissionError):
            public_url_for_file(sentinel.file_id)

        assert (
            module_item_configuration.get_canvas_mapped_file_id(sentinel.file_id)
            == sentinel.file_id
        )

    @pytest.fixture
    def module_item_configuration(self, db_session):
        module_item_configuration = factories.ModuleItemConfiguration()
        db_session.flush()
        return module_item_configuration

    @pytest.fixture
    def with_mapped_file_id(self, module_item_configuration):
        module_item_configuration.set_canvas_mapped_file_id(
            sentinel.file_id, sentinel.mapped_file_id
        )

    @pytest.fixture
    def public_url_for_file(self, canvas_service, module_item_configuration):
        return partial(
            canvas_service.public_url_for_file,
            module_item_configuration,
            course_id=sentinel.course_id,
        )

    @pytest.fixture(autouse=True)
    def CanvasFileFinder(self, patch):
        return patch("lms.services.canvas.CanvasFileFinder")

    @pytest.fixture
    def canvas_file_finder(self, CanvasFileFinder):
        return CanvasFileFinder.return_value


class TestCanvasFileFinder:
    def test_assert_file_in_course_doesnt_raise_if_the_file_is_in_the_course(
        self, finder, canvas_api_client
    ):
        canvas_api_client.list_files.return_value = [
            {"id": sentinel.file_id},
            {"id": sentinel.other_file_id},
        ]

        finder.assert_file_in_course(sentinel.course_id, str(sentinel.file_id))

    def test_assert_file_in_course_raises_if_the_file_isnt_in_the_course(
        self, finder, canvas_api_client
    ):
        canvas_api_client.list_files.return_value = [{"id": sentinel.other_file_id}]

        with pytest.raises(CanvasFileNotFoundInCourse):
            finder.assert_file_in_course(sentinel.course_id, sentinel.file_id)

    def test_find_matching_file_in_course_returns_the_matching_file_id(
        self, finder, canvas_api_client, file_service
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

        matching_file_id = finder.find_matching_file_in_course(
            sentinel.course_id, [sentinel.file_id]
        )

        file_service.get.assert_called_once_with(sentinel.file_id, type_="canvas_file")
        canvas_api_client.list_files.assert_called_once_with(sentinel.course_id)
        assert matching_file_id == str(sentinel.matching_file_id)

    def test_find_matching_file_in_course_with_multiple_file_ids(
        self, finder, canvas_api_client, file_service
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

        matching_file_id = finder.find_matching_file_in_course(
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
        self, finder, file_service
    ):
        file_service.get.return_value = None

        assert not finder.find_matching_file_in_course(
            sentinel.course_id, [sentinel.file_id]
        )

    def test_find_matching_file_in_course_returns_None_if_theres_no_match(
        self, finder, file_service
    ):
        file_service.get.return_value = factories.File(name="foo")

        assert not finder.find_matching_file_in_course(
            sentinel.course_id, [sentinel.file_id]
        )

    def test_find_matching_file_in_course_doesnt_return_the_same_file(
        self, finder, canvas_api_client, file_service
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

        assert not finder.find_matching_file_in_course(
            sentinel.course_id, [sentinel.file_id]
        )

    @pytest.fixture
    def finder(self, canvas_api_client, file_service):
        return CanvasFileFinder(canvas_api_client, file_service)


class TestFactory:
    def test_it(self, pyramid_request, CanvasService, canvas_api_client, file_service):
        result = factory("*any*", request=pyramid_request)

        assert result == CanvasService.return_value
        CanvasService.assert_called_once_with(
            canvas_api=canvas_api_client, file_service=file_service
        )

    @pytest.fixture
    def CanvasService(self, patch):
        return patch("lms.services.canvas.CanvasService")


@pytest.fixture
def canvas_service(canvas_api_client, file_service):
    return CanvasService(canvas_api_client, file_service)
