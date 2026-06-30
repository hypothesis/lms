import pytest

from lms.models import AssignmentCheckpoint
from tests import factories


class TestAssignmentCheckpoint:
    def test_it(self, db_session, assignment):
        db_session.commit()  # Ensure our objects have ids

        checkpoint = AssignmentCheckpoint(assignment=assignment)
        db_session.add(checkpoint)

        db_session.flush()
        assert checkpoint.assignment == assignment
        assert checkpoint.assignment_id == assignment.id
        # reveal_date is NULL until the instructor reveals the assignment.
        assert checkpoint.reveal_date is None

    def test_factory(self, db_session):
        checkpoint = factories.AssignmentCheckpoint()

        db_session.flush()
        assert checkpoint.assignment_id is not None

    @pytest.fixture
    def assignment(self):
        return factories.Assignment.create()
