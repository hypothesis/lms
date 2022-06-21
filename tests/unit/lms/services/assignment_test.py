from datetime import datetime, timedelta
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.models import AssignmentGrouping, AssignmentMembership, LTIParams
from lms.services.assignment import AssignmentService, factory
from tests import factories


class TestAssignmentService:
    def test_get_assignment(self, svc, assignment, matching_params):
        assert svc.get_assignment(**matching_params) == assignment

    def test_get_assignment_without_match(self, svc, non_matching_params):
        assert svc.get_assignment(**non_matching_params) is None

    upsert_kwargs = {
        "document_url": "new_document_url",
        "extra": {"new": "values"},
        "is_gradable": True,
        "lti_params": LTIParams(
            {
                "resource_link_title": "title",
                "resource_link_description": "description",
            }
        ),
    }

    upsert_attrs = {
        "document_url": upsert_kwargs["document_url"],
        "extra": upsert_kwargs["extra"],
        "title": upsert_kwargs["lti_params"]["resource_link_title"],
        "description": upsert_kwargs["lti_params"]["resource_link_description"],
        "is_gradable": upsert_kwargs["is_gradable"],
    }

    def test_upsert_assignment_with_existing(
        self, svc, db_session, assignment, matching_params
    ):
        result = svc.upsert_assignment(**matching_params, **self.upsert_kwargs)

        assert result == assignment
        db_session.flush()
        db_session.refresh(assignment)
        Any.assert_on_comparison = True
        assert assignment == Any.object.with_attrs(self.upsert_attrs)
        assert assignment.created < datetime.now() - timedelta(days=1)
        assert assignment.updated >= datetime.now() - timedelta(days=1)

    def test_upsert_assignment_with_new(
        self, svc, db_session, assignment, non_matching_params
    ):
        result = svc.upsert_assignment(**non_matching_params, **self.upsert_kwargs)

        assert result != assignment
        db_session.flush()
        db_session.refresh(result)
        assert result == Any.object.with_attrs(
            dict(non_matching_params, **self.upsert_attrs)
        )

        assert result.created >= datetime.now() - timedelta(days=1)
        assert result.updated >= datetime.now() - timedelta(days=1)

    def test_upsert_assignment_membership(self, svc, assignment, user):
        lti_roles = factories.LTIRole.create_batch(3)
        # One existing row
        factories.AssignmentMembership.create(
            assignment=assignment, user=user, lti_role=lti_roles[0]
        )

        membership = svc.upsert_assignment_membership(
            assignment=assignment, user=user, lti_roles=lti_roles
        )
        assert (
            membership
            == Any.list.containing(
                [
                    Any.instance_of(AssignmentMembership).with_attrs(
                        {"user": user, "assignment": assignment, "lti_role": lti_role}
                    )
                    for lti_role in lti_roles
                ]
            ).only()
        )

    def test_upsert_assignment_grouping(self, svc, assignment):
        groupings = factories.CanvasGroup.create_batch(3)
        # One existing row
        factories.AssignmentGrouping.create(
            assignment=assignment, grouping=groupings[0]
        )

        refs = svc.upsert_assignment_groupings(assignment, groupings)

        assert refs == Any.list.containing(
            [
                Any.instance_of(AssignmentGrouping).with_attrs(
                    {"assignment": assignment, "grouping": grouping}
                )
                for grouping in groupings
            ]
        )

    @pytest.fixture
    def svc(self, db_session):
        return AssignmentService(db_session)

    @pytest.fixture(autouse=True)
    def assignment(self):
        return factories.Assignment(
            created=datetime(2000, 1, 1), updated=datetime(2000, 1, 1)
        )

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
