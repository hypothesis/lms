import uuid
from unittest.mock import sentinel

import pytest

from lms.models import Assignment
from lms.services.assignment import AssignmentService, factory
from tests import factories


class TestAssignmentService:
    def test_get_without_ids(self, svc, assignment):
        assignment = svc.get(
            assignment.tool_consumer_instance_guid,
            resource_link_id=None,
            ext_lti_assignment_id=None,
        )

        assert assignment is None

    def test_get_returns_None_if_theres_no_matching_assignment(self, svc):
        retrieved_assignment = svc.get(
            "TOOL_CONSUMER_INSTANCE_GUID", "RESOURCE_LINK_ID"
        )

        assert retrieved_assignment is None

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

    def test_get_by_both_ids_not_launched(self, svc, assignment_canvas_not_launched):
        assert assignment_canvas_not_launched.resource_link_id is None

        retrieved_assignment = svc.get(
            assignment_canvas_not_launched.tool_consumer_instance_guid,
            resource_link_id="RESOURCE_LINK_ID",
            ext_lti_assignment_id=assignment_canvas_not_launched.ext_lti_assignment_id,
        )

        assert retrieved_assignment == assignment_canvas_not_launched
        assert assignment_canvas_not_launched.resource_link_id == "RESOURCE_LINK_ID"

    def test_get_by_both_ids_launched(self, svc, assignment_canvas):
        retrieved_assignment = svc.get(
            assignment_canvas.tool_consumer_instance_guid,
            resource_link_id=assignment_canvas.resource_link_id,
            ext_lti_assignment_id=assignment_canvas.ext_lti_assignment_id,
        )
        assert retrieved_assignment == assignment_canvas

    def test_get_merge_existing(self, svc, assignment, assignment_canvas_not_launched):
        # pylint:disable=protected-access
        # Make both assignments belong to the same school
        assignment.tool_consumer_instance_guid = (
            assignment_canvas_not_launched.tool_consumer_instance_guid
        )
        svc._db.flush()
        assert svc._db.query(Assignment).count() == 3 + 2  # noise + fixtures

        retrieved_assignment = svc.get(
            assignment_canvas_not_launched.tool_consumer_instance_guid,
            resource_link_id=assignment.resource_link_id,
            ext_lti_assignment_id=assignment_canvas_not_launched.ext_lti_assignment_id,
        )

        # We merged both into the newest one, the one with a non-null ext_lti_assignment_id
        assert retrieved_assignment.id == assignment_canvas_not_launched.id
        assert retrieved_assignment.resource_link_id == assignment.resource_link_id
        assert svc._db.query(Assignment).count() == 3 + 1  # Deleted one assigment

    def test_create(self, svc):
        assignment = svc.create(
            "TOOL_CONSUMER_INSTANCE_GUID",
            "NEW_DOCUMENT_URL",
            "RESOURCE_LINK_ID",
            "EXT_LTI_ASSIGNMENT_ID",
        )

        assert (
            svc._db.query(Assignment)  # pylint:disable=protected-access
            .filter_by(
                tool_consumer_instance_guid="TOOL_CONSUMER_INSTANCE_GUID",
                resource_link_id="RESOURCE_LINK_ID",
                ext_lti_assignment_id="EXT_LTI_ASSIGNMENT_ID",
                document_url="NEW_DOCUMENT_URL",
            )
            .one()
            == assignment
        )

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
            "NEW_DOCUMENT_URL",
            "RESOURCE_LINK_ID",
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
            "NEW_DOCUMENT_URL",
            assignment.resource_link_id,
        )

        assert assignment.document_url == "NEW_DOCUMENT_URL"

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
