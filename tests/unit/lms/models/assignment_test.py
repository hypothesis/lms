import datetime

import pytest

from lms.models import Assignment
from tests import factories


class TestAssignment:
    def test_set_canvas_mapped_file_id_creates_a_new_mapping_if_none_exists(
        self, assignment
    ):
        assignment.set_canvas_mapped_file_id("original_file_id", "mapped_file_id")

        assert (
            assignment.get_canvas_mapped_file_id("original_file_id") == "mapped_file_id"
        )

    def test_set_canvas_mapped_file_id_overwrites_an_existing_mapping_if_one_exists(
        self, assignment
    ):
        assignment.set_canvas_mapped_file_id("original_file_id", "mapped_file_id")

        assignment.set_canvas_mapped_file_id("original_file_id", "new_mapped_file_id")

        assert (
            assignment.get_canvas_mapped_file_id("original_file_id")
            == "new_mapped_file_id"
        )

    def test_get_canvas_mapped_file_id_returns_the_given_file_id_if_no_mapping_exists(
        self, assignment
    ):
        assert assignment.get_canvas_mapped_file_id("file_id") == "file_id"

    def test_course(self, assignment, db_session):
        course = factories.Course(created=datetime.datetime(2024, 1, 1))
        factories.AssignmentGrouping(
            assignment=assignment, grouping=factories.CanvasSection()
        )
        factories.AssignmentGrouping(
            assignment=assignment, grouping=factories.CanvasGroup()
        )
        factories.AssignmentGrouping(
            assignment=assignment,
            grouping=factories.Course(created=datetime.datetime(2022, 1, 1)),
        )
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        db_session.flush()

        assert assignment.course == course

    @pytest.fixture
    def assignment(self, db_session):
        assignment = Assignment(
            resource_link_id="resource_link_id",
            tool_consumer_instance_guid="tool_consumer_instance_guid",
            document_url="document_url",
        )
        db_session.add(assignment)
        db_session.flush()
        return assignment
