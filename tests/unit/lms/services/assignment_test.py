import uuid
from unittest.mock import sentinel

import pytest
from sqlalchemy.orm.exc import NoResultFound

from lms.models import Assignment
from lms.services.assignment import AssignmentService, factory
from tests import factories


class TestAssignmentService:
    def test_get_without_ids(self, svc, assignment):
        with pytest.raises(ValueError):
            assignment = svc.get(
                assignment.tool_consumer_instance_guid,
                resource_link_id=None,
                ext_lti_assignment_id=None,
            )

    def test_get_raises_NoResultFound_if_theres_no_matching_assignment(self, svc):
        with pytest.raises(NoResultFound):
            svc.get("TOOL_CONSUMER_INSTANCE_GUID", "RESOURCE_LINK_ID")

    def test_get_raises_NoResultFound_if_theres_no_matching_assignment_with_two_ids(
        self, svc
    ):
        with pytest.raises(NoResultFound):
            svc.get(
                "TOOL_CONSUMER_INSTANCE_GUID",
                "RESOURCE_LINK_ID",
                "EXT_LTI_ASSIGNMENT_ID",
            )

    def test_get_by_resource_link_id_only(self, svc, assignment):
        retrieved_assignment = svc.get(
            assignment.tool_consumer_instance_guid, assignment.resource_link_id
        )

        assert retrieved_assignment == assignment

    def test_get_by_ext_lti_id_only(self, svc, assignment_canvas_not_launched):
        retrieved_assignment = svc.get(
            assignment_canvas_not_launched.tool_consumer_instance_guid,
            ext_lti_assignment_id=assignment_canvas_not_launched.ext_lti_assignment_id,
        )

        assert retrieved_assignment == assignment_canvas_not_launched

    def test_get_by_both_ids_no_results(self, svc):
        with pytest.raises(NoResultFound):
            svc.get(
                "tool_consumer_instance_guid",
                resource_link_id="RESOURCE_LINK_ID",
                ext_lti_assignment_id="ext_lti_assignment_id",
            )

    def test_get_by_both_ids_not_launched(self, svc, assignment_canvas_not_launched):
        assert assignment_canvas_not_launched.resource_link_id is None

        retrieved_assignment = svc.get(
            assignment_canvas_not_launched.tool_consumer_instance_guid,
            resource_link_id="RESOURCE_LINK_ID",
            ext_lti_assignment_id=assignment_canvas_not_launched.ext_lti_assignment_id,
        )
        assert retrieved_assignment == assignment_canvas_not_launched

    def test_get_by_both_ids_launched(self, svc, assignment_canvas):
        retrieved_assignment = svc.get(
            assignment_canvas.tool_consumer_instance_guid,
            resource_link_id=assignment_canvas.resource_link_id,
            ext_lti_assignment_id=assignment_canvas.ext_lti_assignment_id,
        )
        assert retrieved_assignment == assignment_canvas

    @pytest.mark.parametrize(
        "old_extra,new_extra",
        [
            ({}, {}),
            ({"somedata": "not copied"}, {}),
            ({"canvas_file_mappings": {1: 2}}, {"canvas_file_mappings": {1: 2}}),
        ],
    )
    def test_merge_canvas_assignments(
        self,
        old_extra,
        new_extra,
        svc,
        assignment,
        assignment_canvas_not_launched,
        db_session,
    ):
        # Make both assignments belong to the same school
        assignment.tool_consumer_instance_guid = (
            assignment_canvas_not_launched.tool_consumer_instance_guid
        )
        assignment.extra = old_extra
        db_session.flush()
        assert db_session.query(Assignment).count() == 3 + 2  # noise + fixtures

        merged_assignment = svc.merge_canvas_assignments(
            assignment, assignment_canvas_not_launched
        )

        # We merged both into the newest one, the one with a non-null ext_lti_assignment_id
        assert merged_assignment.id == assignment_canvas_not_launched.id
        assert merged_assignment.resource_link_id == assignment.resource_link_id
        assert merged_assignment.extra == new_extra
        assert db_session.query(Assignment).count() == 3 + 1  # Deleted one assignment

    def test_exist_with_no_assignment(self, svc):
        assert not svc.exists("TOOL_CONSUMER_INSTANCE_GUID", "RESOURCE_LINK_ID")

    def test_exists_with_assignment(self, svc, assignment):
        assert svc.exists(
            assignment.tool_consumer_instance_guid, assignment.resource_link_id
        )

    def test_exist_with_duplicates(
        self,
        svc,
        db_session,
        assignment,
        assignment_canvas_not_launched,
    ):
        # Make both assignments belong to the same school
        assignment.tool_consumer_instance_guid = (
            assignment_canvas_not_launched.tool_consumer_instance_guid
        )
        db_session.flush()

        assert svc.exists(
            assignment.tool_consumer_instance_guid,
            assignment.resource_link_id,
            assignment_canvas_not_launched.ext_lti_assignment_id,
        )

    def test_set_document_url_saves_the_document_url(self, svc):
        svc.set_document_url(
            "NEW_DOCUMENT_URL",
            "TOOL_CONSUMER_INSTANCE_GUID",
            "RESOURCE_LINK_ID",
        )

        assert (
            svc.get("TOOL_CONSUMER_INSTANCE_GUID", "RESOURCE_LINK_ID").document_url
            == "NEW_DOCUMENT_URL"
        )

    def test_set_document_url_overwrites_an_existing_document_url(
        self, svc, assignment
    ):
        svc.set_document_url(
            "NEW_DOCUMENT_URL",
            assignment.tool_consumer_instance_guid,
            assignment.resource_link_id,
        )

        assert assignment.document_url == "NEW_DOCUMENT_URL"

    def test_set_document_url_with_extra(self, svc, assignment):
        svc.set_document_url(
            "NEW_DOCUMENT_URL",
            assignment.tool_consumer_instance_guid,
            assignment.resource_link_id,
            extra={"some": "value"},
        )

        assert assignment.extra["some"] == "value"

    @pytest.fixture
    def assignment(self):
        return factories.Assignment()

    @pytest.fixture
    def assignment_canvas_not_launched(self):
        return factories.Assignment(
            resource_link_id=None, ext_lti_assignment_id=str(uuid.uuid4())
        )

    @pytest.fixture
    def assignment_canvas(self):
        return factories.Assignment(ext_lti_assignment_id=str(uuid.uuid4()))

    @pytest.fixture(autouse=True)
    def noise(self):
        factories.Assignment.create_batch(size=3)

    @pytest.fixture
    def svc(self, db_session):
        return AssignmentService(db_session)


class TestFactory:
    def test_it(self, pyramid_request):
        assignment_service = factory(sentinel.context, pyramid_request)

        assert isinstance(assignment_service, AssignmentService)
