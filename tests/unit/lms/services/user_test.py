from datetime import datetime
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.models import RoleScope, RoleType, User
from lms.services import UserService
from lms.services.user import UserNotFound, factory
from tests import factories


class TestUserService:
    @pytest.mark.usefixtures("user_is_instructor")
    def test_upsert_user(self, service, lti_user, db_session):
        user = service.upsert_user(lti_user)

        saved_user = db_session.query(User).order_by(User.id.desc()).first()
        assert saved_user == Any.instance_of(User).with_attrs(
            {
                "id": Any.int(),
                "application_instance_id": lti_user.application_instance_id,
                "created": Any.instance_of(datetime),
                "updated": Any.instance_of(datetime),
                "user_id": lti_user.user_id,
                "roles": lti_user.roles,
                "h_userid": lti_user.h_user.userid("authority.example.com"),
                "email": lti_user.email,
                "display_name": lti_user.display_name,
            }
        )
        assert saved_user == user

    @pytest.mark.usefixtures("user_is_learner")
    def test_upsert_user_doesnt_save_email_for_students(
        self, service, lti_user, db_session
    ):
        service.upsert_user(lti_user)

        saved_user = db_session.query(User).order_by(User.id.desc()).first()
        assert saved_user.roles == lti_user.roles
        assert not saved_user.email

    @pytest.mark.usefixtures("user")
    def test_upsert_user_with_an_existing_user(self, service, lti_user, db_session):
        user = service.upsert_user(lti_user)

        saved_user = db_session.get(User, user.id)
        assert saved_user.id == user.id
        assert saved_user.roles == lti_user.roles
        assert user == saved_user

    @pytest.mark.usefixtures("user")
    def test_upsert_user_doesnt_save_email_for_existing_students(
        self, service, lti_user, db_session
    ):
        lti_user.roles = "Student"

        service.upsert_user(lti_user)

        saved_user = db_session.query(User).order_by(User.id.desc()).first()
        assert saved_user.roles == lti_user.roles
        assert not saved_user.email

    def test_get(self, user, service):
        db_user = service.get(user.application_instance, user.user_id)

        assert db_user == user

    def test_get_not_found(self, user, service):
        with pytest.raises(UserNotFound):
            service.get(user.application_instance, "some-other-id")

    def test_get_users(self, service, db_session):
        assignment = factories.Assignment()
        student = factories.User()
        factories.User(h_userid=student.h_userid)  # Duplicated student
        teacher = factories.User()
        factories.AssignmentMembership.create(
            assignment=assignment,
            user=student,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )
        factories.AssignmentMembership.create(
            assignment=assignment,
            user=teacher,
            lti_role=factories.LTIRole(
                scope=RoleScope.COURSE, type=RoleType.INSTRUCTOR
            ),
        )

        query = service.get_users(
            role_scope=RoleScope.COURSE, role_type=RoleType.LEARNER
        )

        assert db_session.scalars(query).all() == [student]

    def test_get_users_by_h_userids(
        self, service, db_session, student_in_assigment, assignment
    ):
        other_student = factories.User()
        factories.AssignmentMembership.create(
            assignment=assignment,
            user=other_student,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )
        # Make sure we have in fact two users
        assert db_session.scalars(
            service.get_users(role_scope=RoleScope.COURSE, role_type=RoleType.LEARNER)
        ).all() == [student_in_assigment, other_student]

        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            h_userids=[other_student.h_userid],
        )

        assert db_session.scalars(query).all() == [other_student]

    def test_get_users_by_course_id(
        self, service, db_session, student_in_assigment, assignment
    ):
        course = factories.Course()
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        db_session.flush()

        query = service.get_users(
            role_scope=RoleScope.COURSE, role_type=RoleType.LEARNER, course_id=course.id
        )

        assert db_session.scalars(query).all() == [student_in_assigment]

    def test_get_users_by_assigment_id(self, service, db_session):
        assignment = factories.Assignment()
        student = factories.User()
        factories.User(h_userid=student.h_userid)  # Duplicated student
        teacher = factories.User()
        factories.AssignmentMembership.create(
            assignment=assignment,
            user=student,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )
        factories.AssignmentMembership.create(
            assignment=assignment,
            user=teacher,
            lti_role=factories.LTIRole(
                scope=RoleScope.COURSE, type=RoleType.INSTRUCTOR
            ),
        )
        db_session.flush()

        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            assignment_id=assignment.id,
        )

        assert db_session.scalars(query).all() == [student]

    def test_get_users_by_instructor_h_userid(
        self,
        service,
        db_session,
        student_in_assigment,
        teacher_in_assigment,
    ):
        # Assignment the h_userid does not belong to
        other_assignment = factories.Assignment()
        other_student = factories.User()
        factories.AssignmentMembership.create(
            assignment=other_assignment,
            user=other_student,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )

        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            instructor_h_userid=teacher_in_assigment.h_userid,
        )

        assert db_session.scalars(query).all() == [student_in_assigment]

    @pytest.fixture
    def assignment(self):
        return factories.Assignment()

    @pytest.fixture
    def student_in_assigment(self, assignment):
        student = factories.User()
        factories.AssignmentMembership.create(
            assignment=assignment,
            user=student,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )
        return student

    @pytest.fixture
    def teacher_in_assigment(self, assignment):
        teacher = factories.User()
        factories.AssignmentMembership.create(
            assignment=assignment,
            user=teacher,
            lti_role=factories.LTIRole(
                scope=RoleScope.COURSE, type=RoleType.INSTRUCTOR
            ),
        )
        return teacher

    @pytest.fixture
    def user(self, lti_user, application_instance):
        return factories.User(
            application_instance=application_instance,
            user_id=lti_user.user_id,
            h_userid=lti_user.h_user.userid("authority.example.com"),
            roles="old_roles",
        )

    @pytest.fixture
    def service(self, db_session):
        return UserService(db_session, h_authority="authority.example.com")


class TestFactory:
    def test_it(self, pyramid_request, UserService):
        user_service = factory(sentinel.context, pyramid_request)

        UserService.assert_called_once_with(
            pyramid_request.db, pyramid_request.registry.settings["h_authority"]
        )
        assert user_service == UserService.return_value

    @pytest.fixture(autouse=True)
    def UserService(self, patch):
        return patch("lms.services.user.UserService")
