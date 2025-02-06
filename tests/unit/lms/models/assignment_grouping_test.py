import pytest
from sqlalchemy.exc import IntegrityError

from lms.models.assignment_grouping import AssignmentGrouping
from tests import factories


class TestAssignmentGrouping:
    def test_it(self, db_session, assignment, grouping):
        db_session.commit()  # Ensure our objects have ids

        rel = AssignmentGrouping(assignment=assignment, grouping=grouping)
        db_session.add(rel)

        db_session.flush()
        assert rel.assignment == assignment
        assert rel.assignment_id == assignment.id
        assert rel.grouping == grouping
        assert rel.grouping_id == grouping.id

    @pytest.mark.filterwarnings(
        "ignore:transaction already deassociated from connection"
    )
    def test_it_does_not_allow_duplicates(self, db_session, assignment, grouping):
        db_session.add(AssignmentGrouping(assignment=assignment, grouping=grouping))
        db_session.commit()

        with pytest.raises(IntegrityError):  # noqa: PT012
            db_session.add(AssignmentGrouping(assignment=assignment, grouping=grouping))
            db_session.commit()

    @pytest.fixture
    def assignment(self):
        return factories.Assignment.create()

    @pytest.fixture
    def grouping(self):
        return factories.CanvasGroup.create()
