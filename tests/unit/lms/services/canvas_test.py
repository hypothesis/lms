import functools
from unittest.mock import call, sentinel

import pytest

from lms.services import (
    CanvasAPIPermissionError,
    CanvasFileNotFoundInCourse,
    CanvasService,
)
from lms.services.canvas import factory
from tests import factories


class TestCanvasServicePublicURLForFile:
    def test_it(self, canvas_service, assignment):
        # We'll demonstrate the full call here, other tests use a caller pattern
        # to make the tests more compact
        result = canvas_service.public_url_for_file(
            file_id="FILE_ID",
            course_id="COURSE_ID",
            resource_link_id=assignment.resource_link_id,
            check_in_course=False,
        )

        assert result == canvas_service.api.public_url.return_value
        canvas_service.api.public_url.assert_called_once_with("FILE_ID")

    def test_total_failure(self, canvas_service, public_url_for_file, db_session, file):
        # Ensure there's no file to match against
        db_session.delete(file)
        # Ensure the API fails consistently
        canvas_service.api.public_url.side_effect = CanvasAPIPermissionError

        with pytest.raises(CanvasAPIPermissionError):
            public_url_for_file()

    def test_it_with_pre_mapped_file(
        self, canvas_service, public_url_for_file, assignment
    ):
        assignment.extra.set("canvas", "file_mapping", {"OLD_ID": "NEW_ID"})

        public_url_for_file(file_id="OLD_ID")

        canvas_service.api.public_url.assert_called_once_with("NEW_ID")

    def test_it_with_check_in_course_and_file_in_course(
        self, canvas_service, public_url_for_file, file
    ):
        canvas_service.api.list_files.return_value = [{"id": file.lms_id}]

        public_url_for_file(file_id=file.lms_id, check_in_course=True)

        canvas_service.api.list_files.assert_called_once_with("COURSE_ID")

    def test_it_with_check_in_course_and_file_not_in_course(self, public_url_for_file):
        with pytest.raises(CanvasFileNotFoundInCourse):
            public_url_for_file(check_in_course=True)

    @pytest.mark.usefixtures("with_matching_mapping")
    def test_it_can_map_a_file_from_file_id(
        self, canvas_service, public_url_for_file, assignment, file
    ):
        # We do the detailed testing of the matching here, although the same
        # can happen in a different location with `check_in_course` True.
        canvas_service.api.public_url.side_effect = (
            CanvasAPIPermissionError,
            sentinel.happy_response,
        )

        response = public_url_for_file(file_id=file.lms_id, check_in_course=False)

        assert response == sentinel.happy_response
        assert canvas_service.api.public_url.call_args_list == [
            # We looked for `file.lms_id` here because it was file_id requested
            call(file.lms_id),
            # Then we looked up the result of mapping when it failed
            call("perfect_match"),
        ]
        assert assignment.extra.get("canvas", "file_mapping") == {
            file.lms_id: "perfect_match"
        }

    @pytest.mark.usefixtures("with_matching_mapping")
    def test_it_can_map_a_file_from_mapping_target(
        self, canvas_service, public_url_for_file, assignment, file
    ):
        # We do the detailed testing of the matching here, although the same
        # can happen in a different location with `check_in_course` True.
        canvas_service.api.public_url.side_effect = (
            CanvasAPIPermissionError,
            sentinel.happy_response,
        )

        assignment.extra.set("canvas", "file_mapping", {"OLD_ID": file.lms_id})

        response = public_url_for_file(file_id="OLD_ID", check_in_course=False)

        assert response == sentinel.happy_response
        assert canvas_service.api.public_url.call_args_list == [
            # We looked for `file.lms_id` here because it was the map target
            call(file.lms_id),
            # Then we looked up the result of mapping when it failed
            call("perfect_match"),
        ]
        assert assignment.extra.get("canvas", "file_mapping") == {
            "OLD_ID": "perfect_match"
        }

    @pytest.mark.usefixtures("with_matching_mapping")
    def test_it_only_maps_once_with_check_in_course(
        self, canvas_service, public_url_for_file
    ):
        canvas_service.api.public_url.side_effect = (
            CanvasAPIPermissionError,
            sentinel.happy_response,
        )

        with pytest.raises(CanvasAPIPermissionError):
            public_url_for_file(check_in_course=True)

        # We can tell we bailed out the first time by checking how many times
        # we called public_url
        canvas_service.api.public_url.assert_called_once_with("perfect_match")

    @pytest.fixture
    def with_matching_mapping(self, canvas_service, file):
        # Add some matching and non-matching examples
        canvas_service.api.list_files.return_value = [
            {"id": "wrong_name", "display_name": "wrong", "size": file.size},
            {"id": "wrong_size", "display_name": file.name, "size": "99999"},
            {"id": "perfect_match", "display_name": file.name, "size": file.size},
        ]

    @pytest.fixture
    def application_instance(self, application_instance_service):
        application_instance = application_instance_service.get.return_value
        application_instance.id = "12345678"

        return application_instance

    @pytest.fixture
    def assignment(self):
        return factories.ModuleItemConfiguration()

    @pytest.fixture
    def assignment_service(self, assignment_service, assignment):
        assignment_service.get.return_value = assignment
        return assignment_service

    @pytest.fixture
    def file(self, application_instance, db_session):
        file = factories.File(
            application_instance_id=application_instance.id, type="canvas_file"
        )
        db_session.flush()
        return file

    @pytest.fixture
    def public_url_for_file(self, canvas_service, assignment, file):
        return functools.partial(
            canvas_service.public_url_for_file,
            file_id=file.lms_id,
            course_id="COURSE_ID",
            resource_link_id=assignment.resource_link_id,
            check_in_course=False,
        )

    @pytest.fixture
    def canvas_service(
        self,
        db_session,
        canvas_api_client,
        application_instance_service,
        assignment_service,
    ):
        canvas_service = CanvasService(
            application_instance_service=application_instance_service,
            assignment_service=assignment_service,
            canvas_api=canvas_api_client,
            db_session=db_session,
        )

        canvas_service.api.list_files.return_value = []

        return canvas_service


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        CanvasService,
        canvas_api_client,
        application_instance_service,
        assignment_service,
    ):
        result = factory(sentinel.context, request=pyramid_request)

        assert result == CanvasService.return_value
        CanvasService.assert_called_once_with(
            canvas_api=canvas_api_client,
            application_instance_service=application_instance_service,
            assignment_service=assignment_service,
            db_session=pyramid_request.db,
        )

    @pytest.fixture
    def CanvasService(self, patch):
        return patch("lms.services.canvas.CanvasService")
