from unittest.mock import sentinel

import pytest

from lms.models import Assignment
from lms.services.assignment import AssignmentService, factory
from tests import factories

MATCHING_TOOL_CONSUMER_INSTANCE_GUID = "matching_tool_consumer_instance_guid"
MATCHING_RESOURCE_LINK_ID = "matching_resource_link_id"


class TestGet:
    def test_it(self, svc):
        matching_assignment = factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
        )

        returned_assignment = svc.get(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
        )

        assert returned_assignment == matching_assignment

    def test_no_matching_assignment(self, svc):
        returned_assignment = svc.get(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
        )

        assert returned_assignment is None

    def test_assignment_has_different_tool_consumer_instance_guid(self, svc):
        factories.Assignment(
            tool_consumer_instance_guid="different",
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
        )

        returned_assignment = svc.get(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID, MATCHING_RESOURCE_LINK_ID
        )

        assert returned_assignment is None


class TestExists:
    def test_existing(self, svc):
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
        )

        result = svc.exists(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID, MATCHING_RESOURCE_LINK_ID
        )

        assert result is True

    def test_non_existing(self, svc):
        result = svc.exists(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID, MATCHING_RESOURCE_LINK_ID
        )

        assert not result


class TestUpsertDocumentURL:
    def test_if_theres_no_matching_assignment_it_creates_one(
        self, svc, assert_document_url
    ):
        svc.upsert(
            "new_document_url",
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
        )

        assert_document_url(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
            "new_document_url",
        )

    def test_if_theres_a_matching_assignment_it_updates_it(
        self, svc, assert_document_url
    ):
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
            document_url="old_document_url",
        )

        svc.upsert(
            "new_document_url",
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
        )

        assert_document_url(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
            "new_document_url",
        )

    @pytest.fixture
    def assert_document_url(self, db_session):
        def _assert_document_url(guid, resource_link_id, document_url):
            assert (
                db_session.query(Assignment)
                .filter_by(
                    tool_consumer_instance_guid=guid, resource_link_id=resource_link_id
                )
                .one()
            ).document_url == document_url

        return _assert_document_url


class TestFactory:
    def test_it(self, pyramid_request):
        assignment_service = factory(sentinel.context, pyramid_request)

        assert isinstance(assignment_service, AssignmentService)


@pytest.fixture(autouse=True)
def noise():
    factories.Assignment(
        tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
        resource_link_id="noise_resource_link_id",
    )
    factories.Assignment(
        tool_consumer_instance_guid="noise_tool_consumer_instance_guid",
        resource_link_id=MATCHING_RESOURCE_LINK_ID,
    )


@pytest.fixture
def svc(db_session):
    return AssignmentService(db_session)
