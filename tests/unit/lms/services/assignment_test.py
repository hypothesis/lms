from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.services.assignment import AssignmentService, factory
from tests import factories


class TestAssignmentService:
    def test_get(self, svc, assignment, matching_params):
        assert svc.get(**matching_params) == assignment

    def test_get_without_match(self, svc, non_matching_params):
        assert svc.get(**non_matching_params) is None

    @pytest.mark.usefixtures("assignment")
    def test_exists(self, svc, matching_params):
        assert svc.exists(**matching_params)

    def test_exists_without_match(self, svc, non_matching_params):
        assert not svc.exists(**non_matching_params)

    def test_upsert_with_existing(self, svc, db_session, assignment, matching_params):
        updated_attrs = {"document_url": "new_document_url", "extra": {"new": "values"}}

        result = svc.upsert(**matching_params, **updated_attrs)

        assert result == assignment
        db_session.flush()
        db_session.refresh(assignment)
        assert assignment == Any.object.with_attrs(updated_attrs)

    def test_upsert_with_new(self, svc, db_session, assignment, non_matching_params):
        non_matching_params.update(
            {"document_url": "new_document_url", "extra": {"new": "values"}}
        )

        result = svc.upsert(**non_matching_params)

        assert result != assignment
        db_session.flush()
        db_session.refresh(result)
        assert result == Any.object.with_attrs(non_matching_params)

    @pytest.fixture
    def svc(self, db_session):
        return AssignmentService(db_session)

    @pytest.fixture(autouse=True)
    def assignment(self):
        return factories.Assignment()

    @pytest.fixture
    def matching_params(self, assignment):
        return {
            "tool_consumer_instance_guid": assignment.tool_consumer_instance_guid,
            "resource_link_id": assignment.resource_link_id,
        }

    @pytest.fixture(params=["tool_consumer_instance_guid", "resource_link_id"])
    def non_matching_params(self, request, matching_params):
        non_matching_params = dict(matching_params)
        non_matching_params[request.param] = "NOT_MATCHING"

        return non_matching_params

    @pytest.fixture(autouse=True)
    def with_assignment_noise(self, assignment):
        factories.Assignment(
            tool_consumer_instance_guid=assignment.tool_consumer_instance_guid,
            resource_link_id="noise_resource_link_id",
        )
        factories.Assignment(
            tool_consumer_instance_guid="noise_tool_consumer_instance_guid",
            resource_link_id=assignment.resource_link_id,
        )


class TestFactory:
    def test_it(self, pyramid_request, AssignmentService):
        svc = factory(sentinel.context, pyramid_request)

        AssignmentService.assert_called_once_with(db=pyramid_request.db)
        assert svc == AssignmentService.return_value

    @pytest.fixture
    def AssignmentService(self, patch):
        return patch("lms.services.assignment.AssignmentService")
