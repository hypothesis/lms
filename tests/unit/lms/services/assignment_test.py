from unittest.mock import sentinel

import pytest

from lms.services.assignment import AssignmentService, factory
from tests import factories


class TestAssignmentService:
    def test_get_document_url_returns_the_document_url(self, svc):
        mic = factories.ModuleItemConfiguration()

        document_url = svc.get_document_url(
            mic.tool_consumer_instance_guid, mic.resource_link_id
        )

        assert document_url == mic.document_url

    def test_get_document_url_returns_None_if_theres_no_matching_document_url(
        self, svc
    ):
        document_url = svc.get_document_url(
            "test_tool_consumer_instance_guid", "test_resource_link_id"
        )

        assert document_url is None

    def test_set_document_url_saves_the_document_url(self, svc):
        svc.set_document_url(
            "test_tool_consumer_instance_guid",
            "test_resource_link_id",
            "NEW_DOCUMENT_URL",
        )

        assert (
            svc.get_document_url(
                "test_tool_consumer_instance_guid", "test_resource_link_id"
            )
            == "NEW_DOCUMENT_URL"
        )

    def test_set_document_url_overwrites_an_existing_document_url(self, svc):
        mic = factories.ModuleItemConfiguration()

        svc.set_document_url(
            mic.tool_consumer_instance_guid, mic.resource_link_id, "NEW_DOCUMENT_URL"
        )

        assert mic.document_url == "NEW_DOCUMENT_URL"

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
