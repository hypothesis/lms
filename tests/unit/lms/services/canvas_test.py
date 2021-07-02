from functools import partial
from unittest.mock import DEFAULT, call, sentinel

import pytest

from lms.services import (
    CanvasAPIPermissionError,
    CanvasFileNotFoundInCourse,
    CanvasService,
)
from lms.services.canvas import factory
from tests import factories


class TestPublicURLForFile:
    def test_it(self, canvas_service, public_url_for_file, effective_id):
        url = public_url_for_file(file_id=sentinel.file_id, check_in_course=False)

        canvas_service.file_mapper.assert_file_in_course.assert_not_called()
        canvas_service.api.public_url.assert_called_once_with(effective_id)
        assert url == canvas_service.api.public_url.return_value

    @pytest.mark.usefixtures("with_permission_failure_on_first_call")
    def test_we_map_if_the_first_retrieval_is_unsuccessful(
        self, canvas_service, public_url_for_file, effective_id, assignment
    ):
        url = public_url_for_file(
            file_id=sentinel.file_id, course_id=sentinel.course_id
        )

        canvas_service.file_mapper.map_file.assert_called_once_with(
            effective_id, sentinel.course_id
        )
        assert (
            assignment.get_canvas_mapped_file_id(sentinel.file_id)
            == canvas_service.file_mapper.map_file.return_value
        )
        assert url == canvas_service.api.public_url.return_value

    @pytest.mark.usefixtures("with_file_not_in_course")
    def test_we_map_if_the_file_is_not_in_the_course(
        self, canvas_service, public_url_for_file, effective_id, assignment
    ):
        public_url_for_file(
            file_id=sentinel.file_id, course_id=sentinel.course_id, check_in_course=True
        )

        canvas_service.file_mapper.assert_file_in_course.assert_called_once_with(
            effective_id, sentinel.course_id
        )
        canvas_service.file_mapper.map_file.assert_called_once_with(
            effective_id, sentinel.course_id
        )
        # Don't retest all the things that happen when mappings are done

    @pytest.mark.usefixtures("with_permission_failure_on_first_call")
    def test_we_raise_if_mappings_fails_after_CanvasAPIPermissionError(
        self, canvas_service, public_url_for_file
    ):
        canvas_service.file_mapper.map_file.return_value = None

        with pytest.raises(CanvasAPIPermissionError):
            public_url_for_file()

    @pytest.mark.usefixtures("with_file_not_in_course")
    def test_we_raise_if_mappings_fails_after_CanvasFileNotFoundInCourse(
        self, canvas_service, public_url_for_file
    ):
        canvas_service.file_mapper.map_file.return_value = None

        with pytest.raises(CanvasFileNotFoundInCourse):
            public_url_for_file(check_in_course=True)

    def test_we_do_not_store_a_mapping_if_retrieval_fails(
        self, canvas_service, public_url_for_file, assignment
    ):
        # Set this to fail every time
        canvas_service.api.public_url.side_effect = CanvasAPIPermissionError

        with pytest.raises(CanvasAPIPermissionError):
            public_url_for_file(
                file_id=sentinel.file_id, module_item_configuration=assignment
            )

        assert assignment.get_canvas_mapped_file_id(sentinel.file_id) is None

    @pytest.fixture
    def with_permission_failure_on_first_call(self, canvas_service):
        canvas_service.api.public_url.side_effect = (
            CanvasAPIPermissionError,
            canvas_service.api.public_url.return_value,
        )

    @pytest.fixture
    def with_file_not_in_course(self, canvas_service):
        canvas_service.file_mapper.assert_file_in_course.side_effect = (
            CanvasFileNotFoundInCourse(sentinel.file_id)
        )

    @pytest.fixture(params=(sentinel.file_id, sentinel.mapped_id))
    def effective_id(self, request, assignment):
        if request.param != sentinel.file_id:
            assignment.set_canvas_mapped_file_id(sentinel.file_id, sentinel.mapped_id)

        return request.param

    @pytest.fixture(autouse=True)
    def CanvasFileMapper(self, patch):
        return patch("lms.services.canvas.CanvasFileMapper")

    @pytest.fixture
    def assignment(self, db_session):
        return factories.ModuleItemConfiguration()

    @pytest.fixture
    def canvas_service(self, canvas_api_client, file_service):
        return CanvasService(canvas_api_client, file_service)

    @pytest.fixture
    def public_url_for_file(self, canvas_service, assignment):
        return partial(
            canvas_service.public_url_for_file,
            module_item_configuration=assignment,
            file_id=sentinel.file_id,
            course_id=sentinel.course_id,
        )


class TestCanvasFileMapper:
    # Imagine good tests here...

    def test_map_file_returns_the_id_if_theres_a_matching_file_in_the_course(self):
        ...

    def test_map_file_returns_None_if_theres_no_matching_file_in_the_course(self):
        ...

    def test_assert_file_in_course_does_not_raise_if_the_file_is_in_the_course(self):
        ...

    def test_assert_file_in_course_raises_if_the_file_isnt_in_the_course(self):
        ...


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
