from unittest.mock import sentinel

import pytest

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
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID, MATCHING_RESOURCE_LINK_ID
        )

        assert returned_assignment == matching_assignment

    @pytest.mark.parametrize(
        "guid,resource_link_id",
        [
            ("NO_MATCH_GUID", "NO_MATCH_RESOURCE"),
            (MATCHING_TOOL_CONSUMER_INSTANCE_GUID, "NO_MATCH_RESOURCE"),
            ("NO_MATCH_GUID", MATCHING_RESOURCE_LINK_ID),
        ],
    )
    def test_no_matching_assignment(self, svc, guid, resource_link_id):
        returned_assignment = svc.get(guid, resource_link_id)

        assert returned_assignment is None


class TestExists:
    def test_existent(self, svc):
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
        )

        result = svc.exists(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID, MATCHING_RESOURCE_LINK_ID
        )

        assert result is True

    def test_non_existent(self, svc):
        result = svc.exists(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID, "NON_MATCHING_RESOURCE_LINK_ID"
        )

        assert not result


class TestUpsert:
    def test_inserts_new(self, svc):
        svc.upsert(
            "new_document_url",
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            "SOME_NEW_RESOURCE_LINK_ID",
        )

        assert (
            svc.get(
                MATCHING_TOOL_CONSUMER_INSTANCE_GUID, "SOME_NEW_RESOURCE_LINK_ID"
            ).document_url
            == "new_document_url"
        )

    @pytest.mark.parametrize("extra", [{"some_key": "value"}, {}])
    def test_updates_existing(self, svc, extra):
        factories.Assignment(
            tool_consumer_instance_guid=MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            resource_link_id=MATCHING_RESOURCE_LINK_ID,
            document_url="old_document_url",
        )

        svc.upsert(
            "new_document_url",
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID,
            MATCHING_RESOURCE_LINK_ID,
            extra=extra,
        )

        assigment = svc.get(
            MATCHING_TOOL_CONSUMER_INSTANCE_GUID, MATCHING_RESOURCE_LINK_ID
        )

        assert assigment.document_url == "new_document_url"
        assert assigment.extra == extra


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
