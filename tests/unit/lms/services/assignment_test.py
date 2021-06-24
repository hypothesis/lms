from unittest.mock import sentinel

import pytest

from lms.services.assignment import AssignmentService, factory
from tests import factories


class TestAssignmentService:
    def test_get(self, svc, assignment):
        retrieved_assignment = svc.get(
            assignment.tool_consumer_instance_guid, assignment.resource_link_id
        )

        assert retrieved_assignment == assignment

    def test_get_returns_None_if_theres_no_matching_assignment(self, svc):
        retrieved_assignment = svc.get(
            "TOOL_CONSUMER_INSTANCE_GUID", "RESOURCE_LINK_ID"
        )

        assert retrieved_assignment is None

    def test_get_document_url_returns_the_document_url(self, svc, assignment):
        document_url = svc.get_document_url(
            assignment.tool_consumer_instance_guid, assignment.resource_link_id
        )

        assert document_url == assignment.document_url

    def test_get_document_url_returns_None_if_theres_no_matching_document_url(
        self, svc
    ):
        document_url = svc.get_document_url(
            "TOOL_CONSUMER_INSTANCE_GUID", "RESOURCE_LINK_ID"
        )

        assert document_url is None

    def test_set_document_url_saves_the_document_url(self, svc):
        svc.set_document_url(
            "TOOL_CONSUMER_INSTANCE_GUID",
            "RESOURCE_LINK_ID",
            "NEW_DOCUMENT_URL",
        )

        assert (
            svc.get_document_url("TOOL_CONSUMER_INSTANCE_GUID", "RESOURCE_LINK_ID")
            == "NEW_DOCUMENT_URL"
        )

    def test_set_document_url_overwrites_an_existing_document_url(
        self, svc, assignment
    ):
        svc.set_document_url(
            assignment.tool_consumer_instance_guid,
            assignment.resource_link_id,
            "NEW_DOCUMENT_URL",
        )

        assert assignment.document_url == "NEW_DOCUMENT_URL"

    def test_get_canvas_mapped_file_id_returns_None_if_the_assignment_doesnt_exist(
        self, svc
    ):
        assert not svc.get_canvas_mapped_file_id(
            "unknown_resource_link_id", "unknown_resource_link_id", "file_id"
        )

    def test_set_canvas_mapped_file_id_creates_a_new_mapping_if_none_exists(
        self, assignment, svc
    ):
        svc.set_canvas_mapped_file_id(
            assignment.tool_consumer_instance_guid,
            assignment.resource_link_id,
            "original_file_id",
            "mapped_file_id",
        )

        assert (
            svc.get_canvas_mapped_file_id(
                assignment.tool_consumer_instance_guid,
                assignment.resource_link_id,
                "original_file_id",
            )
            == "mapped_file_id"
        )

    def test_set_canvas_mapped_file_id_overwrites_an_existing_mapping_if_one_exists(
        self, assignment, svc
    ):
        svc.set_canvas_mapped_file_id(
            assignment.tool_consumer_instance_guid,
            assignment.resource_link_id,
            "original_file_id",
            "mapped_file_id",
        )

        svc.set_canvas_mapped_file_id(
            assignment.tool_consumer_instance_guid,
            assignment.resource_link_id,
            "original_file_id",
            "new_mapped_file_id",
        )

        assert (
            svc.get_canvas_mapped_file_id(
                assignment.tool_consumer_instance_guid,
                assignment.resource_link_id,
                "original_file_id",
            )
            == "new_mapped_file_id"
        )

    def test_set_canvas_mapped_file_id_raises_ValueError_if_the_assignment_doesnt_exist(
        self, svc
    ):
        with pytest.raises(ValueError):
            svc.set_canvas_mapped_file_id(
                "unknown_tool_consumer_instance_guid",
                "unknown_resource_link_id",
                "original_file_id",
                "new_mapped_file_id",
            )

    @pytest.fixture
    def assignment(self):
        return factories.ModuleItemConfiguration()

    @pytest.fixture(autouse=True)
    def noise(self):
        factories.ModuleItemConfiguration.create_batch(size=3)

    @pytest.fixture
    def svc(self, db_session):
        return AssignmentService(db_session)


class TestFactory:
    def test_it(self, pyramid_request):
        assignment_service = factory(sentinel.context, pyramid_request)

        assert isinstance(assignment_service, AssignmentService)
