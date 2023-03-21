from datetime import datetime, timedelta

import pytest
from h_matchers import Any

from lms.models.lti_role import RoleScope, RoleType
from lms.services.digest._digest_assistant import DigestAssistant
from lms.services.digest._models import HCourse, HUser
from tests import factories


class TestDigestAssistant:
    def test_get_h_users(self, assistant):
        for days, (userid, email, name) in enumerate(
            (
                ("h_userid_1", None, None),
                ("h_userid_1", "WRONG", "WRONG"),
                ("h_userid_1", "email_1", "name_1"),
                ("h_userid_1", None, None),
                # Check we can get more than one at a time
                ("h_userid_2", "email_2", "name_2"),
            )
        ):
            factories.User(
                h_userid=userid,
                email=email,
                display_name=name,
                # Ensure the insert order is the updated order too
                updated=datetime.now() + timedelta(days=days),
            )

        users = assistant.get_h_users(["h_userid_1", "h_userid_2"])

        print(users)

        assert users == [
            HUser(h_userid="h_userid_1", name="name_1", email="email_1"),
            HUser(h_userid="h_userid_2", name="name_2", email="email_2"),
        ]

    # We need to parameterize here to check we can go from course to group and
    # vice versa, but always end up with the course as the result
    @pytest.mark.parametrize("search_by", ("aid_course", "aid_group"))
    def test_get_h_courses(self, assistant, search_by):
        # Set up a course with a group and a teacher + student
        course = factories.Course(authority_provided_id="aid_course")
        group = factories.CanvasGroup(authority_provided_id="aid_group", parent=course)
        assignment = factories.Assignment()
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        factories.AssignmentGrouping(assignment=assignment, grouping=group)
        instructor = factories.User(h_userid="acct:instructor")
        factories.AssignmentMembership(
            assignment=assignment,
            user=instructor,
            lti_role=factories.LTIRole(
                type=RoleType.INSTRUCTOR, scope=RoleScope.COURSE
            ),
        )
        learner = factories.User(h_userid="acct:learner")
        factories.AssignmentMembership(
            assignment=assignment,
            user=learner,
            lti_role=factories.LTIRole(type=RoleType.LEARNER, scope=RoleScope.COURSE),
        )

        courses = assistant.get_h_courses(
            authority_provided_ids=[search_by, "red_herring"]
        )

        assert courses == [
            HCourse(
                title=course.lms_name,
                authority_provided_id="aid_course",
                aka=Any.list.containing(["aid_course", "aid_group"]).only(),
                instructors=[instructor.h_userid],
            )
        ]

    def test_get_h_courses_with_no_instructor(self, assistant):
        # If a course has no teachers, we don't return it. This is
        # counterintuitive for most use cases, but the SQL is easier, and it
        # works for us. If the course has no teachers, there's nobody to notify
        factories.Course(authority_provided_id="aid")

        assert not assistant.get_h_courses(authority_provided_ids=["aid"])

    @pytest.fixture
    def assistant(self, db_session):
        return DigestAssistant(db_session)
