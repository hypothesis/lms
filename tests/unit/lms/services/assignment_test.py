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

    def test_create_assignment(self, svc, db_session):

        assignment = svc.create_assignment(sentinel.guid, sentinel.resource_link_id)

        assert assignment.tool_consumer_instance_guid == sentinel.guid
        assert assignment.resource_link_id == sentinel.resource_link_id
        assert assignment.extra == {}

        assert assignment in db_session.new

    def test_update_assignment(self, svc):
        assignment = svc.update_assignment(
            factories.Assignment(), sentinel.document_url, sentinel.group_set_id
        )

        assert assignment.document_url == sentinel.document_url
        assert assignment.extra["group_set_id"] == sentinel.group_set_id

    @pytest.mark.parametrize(
        "param",
        (
            "resource_link_id_history",
            "ext_d2l_resource_link_id_history",
            "custom_ResourceLink.id.history",
        ),
    )
    def test_get_copied_from_assignment(self, svc, param, assignment):
        assert (
            svc.get_copied_from_assignment(
                {
                    param: assignment.resource_link_id,
                    "tool_consumer_instance_guid": assignment.tool_consumer_instance_guid,
                }
            )
            == assignment
        )

    def test_get_copied_from_assignment_not_found_bad_parameter(self, svc, assignment):
        assert not svc.get_copied_from_assignment(
            {
                "unknown_param": assignment.resource_link_id,
                "tool_consumer_instance_guid": assignment.tool_consumer_instance_guid,
            }
        )

    def test_get_copied_from_assignment_not_found(self, svc, assignment):
        assert not svc.get_copied_from_assignment(
            {
                "resource_link_id_history": "Unknown_RESOURCE_LINK_ID",
                "tool_consumer_instance_guid": assignment.tool_consumer_instance_guid,
            }
        )

    upsert_kwargs = {
        "document_url": "new_document_url",
        "extra": {"new": "values"},
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
    }

    @pytest.mark.parametrize("is_gradable", [True, False])
    def test_upsert_assignment_with_existing(
        self, svc, db_session, assignment, matching_params, is_gradable, misc_plugin
    ):
        misc_plugin.is_assignment_gradable.return_value = is_gradable

        result = svc.upsert_assignment(**matching_params, **self.upsert_kwargs)

        assert result == assignment
        db_session.flush()
        db_session.refresh(assignment)
        Any.assert_on_comparison = True
        assert assignment == Any.object.with_attrs(self.upsert_attrs)
        assert assignment.created < datetime.now() - timedelta(days=1)
        assert assignment.updated >= datetime.now() - timedelta(days=1)
        assert assignment.is_gradable == is_gradable

    def test_upsert_assignment_with_existing_no_extra(
        self, svc, assignment, matching_params
    ):
        upsert_kwargs = dict(self.upsert_kwargs, extra={})
        result = svc.upsert_assignment(**matching_params, **upsert_kwargs)

        assert result == assignment
        assert not result.extra

    @pytest.mark.parametrize("is_gradable", [True, False])
    def test_upsert_assignment_with_new(
        self, svc, db_session, assignment, non_matching_params, is_gradable, misc_plugin
    ):
        misc_plugin.is_assignment_gradable.return_value = is_gradable

        result = svc.upsert_assignment(**non_matching_params, **self.upsert_kwargs)

        assert result != assignment
        db_session.flush()
        db_session.refresh(result)
        assert result == Any.object.with_attrs(
            dict(non_matching_params, **self.upsert_attrs)
        )

        assert result.created >= datetime.now() - timedelta(days=1)
        assert result.updated >= datetime.now() - timedelta(days=1)

    @pytest.mark.parametrize(
        "copied_from_param",
        (
            "resource_link_id_history",
            "ext_d2l_resource_link_id_history",
            "custom_ResourceLink.id.history",
        ),
    )
    @pytest.mark.parametrize(
        "value,expected",
        (
            ("ORIGINAL_ID", "ORIGINAL_ID"),
            ("COPY_OF_ORIGINAL,ORIGINAL_ID", "COPY_OF_ORIGINAL"),
        ),
    )
    def test_upsert_assignment_with_copied_fromr(
        self, svc, copied_from_param, value, expected, db_session
    ):
        upsert_params = dict(
            self.upsert_kwargs,
            resource_link_id="NEW_ID",
            tool_consumer_instance_guid="MATCHING_GUID",
        )
        upsert_params["lti_params"][copied_from_param] = value
        upsert_params["lti_params"]["tool_consumer_instance_guid"] = "MATCHING_GUID"
        original_assignment = factories.Assignment(
            resource_link_id=expected, tool_consumer_instance_guid="MATCHING_GUID"
        )
        db_session.flush()

        new_assignment = svc.upsert_assignment(**upsert_params)

        assert new_assignment != original_assignment
        assert new_assignment.copied_from == original_assignment

    @pytest.mark.parametrize(
        "copied_from_param",
        (
            "resource_link_id_history",
            "ext_d2l_resource_link_id_history",
            "custom_ResourceLink.id.history",
        ),
    )
    def test_upsert_assignment_with_copied_from_extra_parameter(
        self, svc, copied_from_param, db_session
    ):
        upsert_params = dict(
            self.upsert_kwargs,
            resource_link_id="NEW_ID",
            tool_consumer_instance_guid="MATCHING_GUID",
        )
        upsert_params["lti_params"][copied_from_param] = "ORIGINAL_ID"
        upsert_params["lti_params"]["tool_consumer_instance_guid"] = "MATCHING_GUID"
        original_assignment = factories.Assignment(
            resource_link_id="ORIGINAL_ID",
            tool_consumer_instance_guid="MATCHING_GUID",
            extra={
                "group_set_id": "ORIGINAL_GROUP_SET_ID",
                "non_copied_value": "VALUE",
            },
        )
        db_session.flush()

        new_assignment = svc.upsert_assignment(**upsert_params)

        assert new_assignment != original_assignment
        assert new_assignment.extra == dict(
            upsert_params["extra"],
            group_set_id="ORIGINAL_GROUP_SET_ID",
        )

    def test_upsert_assignment_membership(self, svc, assignment):
        user = factories.User()
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

    def test_upsert_assignment_grouping(self, svc, assignment, db_session):
        groupings = factories.CanvasGroup.create_batch(3)
        # One existing row
        factories.AssignmentGrouping.create(
            assignment=assignment, grouping=groupings[0]
        )
        db_session.flush()

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
    def svc(self, db_session, misc_plugin):
        return AssignmentService(db_session, misc_plugin)

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
    def test_it(self, pyramid_request, AssignmentService, misc_plugin):
        svc = factory(sentinel.context, pyramid_request)

        AssignmentService.assert_called_once_with(
            db=pyramid_request.db, misc_plugin=misc_plugin
        )
        assert svc == AssignmentService.return_value

    @pytest.fixture
    def AssignmentService(self, patch):
        return patch("lms.services.assignment.AssignmentService")
