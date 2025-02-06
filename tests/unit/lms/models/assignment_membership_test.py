import pytest
from sqlalchemy.exc import IntegrityError

from lms.models import AssignmentMembership
from tests import factories


class TestAssignmentMembership:
    def test_it(self, db_session, user, assignment, lti_role):
        db_session.commit()  # Ensure our objects have ids

        membership = AssignmentMembership(
            user=user, assignment=assignment, lti_role=lti_role
        )
        db_session.add(membership)

        db_session.flush()
        assert membership.user == user
        assert membership.user_id == user.id
        assert membership.assignment == assignment
        assert membership.assignment_id == assignment.id
        assert membership.lti_role == lti_role
        assert membership.lti_role_id == lti_role.id

    @pytest.mark.filterwarnings(
        "ignore:transaction already deassociated from connection"
    )
    def test_it_does_not_allow_duplicates(self, db_session, user, assignment, lti_role):
        db_session.add(
            AssignmentMembership(user=user, assignment=assignment, lti_role=lti_role)
        )
        db_session.commit()

        with pytest.raises(IntegrityError):  # noqa: PT012
            db_session.add(
                AssignmentMembership(
                    user=user, assignment=assignment, lti_role=lti_role
                )
            )
            db_session.commit()

    @pytest.fixture
    def user(self):
        return factories.User.create()

    @pytest.fixture
    def assignment(self):
        return factories.Assignment.create()

    @pytest.fixture
    def lti_role(self):
        return factories.LTIRole.create()
