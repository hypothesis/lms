from datetime import datetime
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from sqlalchemy import select

from lms.models import LMSUser, RoleScope, RoleType, User
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
        self.assert_lms_user(db_session, user)

    @pytest.mark.usefixtures("user_is_learner")
    def test_upsert_user_doesnt_save_email_for_students(
        self, service, lti_user, db_session
    ):
        service.upsert_user(lti_user)

        saved_user = db_session.query(User).order_by(User.id.desc()).first()
        assert saved_user.roles == lti_user.roles
        assert not saved_user.email
        self.assert_lms_user(db_session, saved_user)

    @pytest.mark.usefixtures("user")
    def test_upsert_user_with_an_existing_user(self, service, lti_user, db_session):
        user = service.upsert_user(lti_user)

        saved_user = db_session.get(User, user.id)
        assert saved_user.id == user.id
        assert saved_user.roles == lti_user.roles
        assert user == saved_user
        self.assert_lms_user(db_session, user)

    @pytest.mark.usefixtures("user")
    def test_upsert_user_doesnt_save_email_for_existing_students(
        self, service, lti_user, db_session
    ):
        lti_user.roles = "Student"

        service.upsert_user(lti_user)

        saved_user = db_session.query(User).order_by(User.id.desc()).first()
        assert saved_user.roles == lti_user.roles
        assert not saved_user.email
        self.assert_lms_user(db_session, saved_user)

    def test_get(self, user, service):
        db_user = service.get(user.application_instance, user.user_id)

        assert db_user == user

    def test_get_not_found(self, user, service):
        with pytest.raises(UserNotFound):
            service.get(user.application_instance, "some-other-id")

    def test_get_users(
        self,
        service,
        db_session,
        organization,
        student_in_assigment,
    ):
        factories.User(h_userid=student_in_assigment.h_userid)  # Duplicated student

        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            admin_organization_ids=[organization.id],
        )

        assert db_session.scalars(query).all() == [student_in_assigment]

    def test_get_users_by_h_userids(
        self, service, db_session, student_in_assigment, assignment, organization
    ):
        other_student = factories.User(
            application_instance=organization.application_instances[0]
        )
        factories.AssignmentMembership.create(
            assignment=assignment,
            user=other_student,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )
        db_session.flush()
        # Make sure we have in fact two users
        assert db_session.scalars(
            service.get_users(
                role_scope=RoleScope.COURSE,
                role_type=RoleType.LEARNER,
                admin_organization_ids=[organization.id],
            )
        ).all() == [student_in_assigment, other_student]

        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            h_userids=[other_student.h_userid],
            admin_organization_ids=[organization.id],
        )

        assert db_session.scalars(query).all() == [other_student]

    @pytest.mark.usefixtures("assignment")
    def test_get_users_by_course_id(
        self, service, db_session, student_in_assigment, course, organization
    ):
        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            course_ids=[course.id],
            admin_organization_ids=[organization.id],
        )

        assert db_session.scalars(query).all() == [student_in_assigment]

    @pytest.mark.usefixtures("teacher_in_assigment")
    def test_get_users_by_assigment_id(
        self, service, db_session, student_in_assigment, assignment, organization
    ):
        factories.User(h_userid=student_in_assigment.h_userid)  # Duplicated student
        db_session.flush()

        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            assignment_ids=[assignment.id],
            admin_organization_ids=[organization.id],
        )

        assert db_session.scalars(query).all() == [student_in_assigment]

    @pytest.mark.usefixtures("assignment", "course")
    def test_get_users_by_instructor_h_userid(
        self, service, db_session, student_in_assigment, teacher_in_assigment
    ):
        # Assignment in another course
        other_assignment = factories.Assignment(course=factories.Course())
        other_student = factories.User()
        factories.AssignmentMembership.create(
            assignment=other_assignment,
            user=other_student,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )
        db_session.flush()

        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            instructor_h_userid=teacher_in_assigment.h_userid,
        )

        assert db_session.scalars(query).all() == [student_in_assigment]

    def assert_lms_user(self, db_session, user):
        """Assert the corresponding LMSUser to user exists in the DB with the same attributes."""

        lms_user = db_session.scalars(
            select(LMSUser).where(LMSUser.h_userid == user.h_userid)
        ).one()

        assert lms_user.display_name == user.display_name
        assert lms_user.email == user.email
        assert lms_user.updated == user.updated

    @pytest.fixture
    def course(self, application_instance, db_session):
        course = factories.Course(application_instance=application_instance)
        db_session.flush()

        return course

    @pytest.fixture
    def assignment(self, course):
        assignment = factories.Assignment(course=course)
        factories.AssignmentGrouping(assignment=assignment, grouping=course)

        return assignment

    @pytest.fixture
    def student_in_assigment(self, assignment, application_instance):
        student = factories.User(application_instance=application_instance)
        factories.AssignmentMembership.create(
            assignment=assignment,
            user=student,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )
        factories.GroupingMembership.create(
            grouping=assignment.course,
            user=student,
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
        user = factories.User(
            application_instance=application_instance,
            user_id=lti_user.user_id,
            h_userid=lti_user.h_user.userid("authority.example.com"),
            roles="old_roles",
        )
        factories.LMSUser(
            tool_consumer_instance_guid=application_instance.tool_consumer_instance_guid,
            lti_user_id=user.user_id,
            h_userid=lti_user.h_user.userid("authority.example.com"),
            email=user.email,
            display_name=user.display_name,
        )
        return user

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
