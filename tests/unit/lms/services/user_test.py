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

    @pytest.mark.parametrize("instructor_h_userid", [True, False])
    @pytest.mark.parametrize("h_userids", [True, False])
    @pytest.mark.parametrize("course_id", [True, False])
    @pytest.mark.parametrize("assignment_id", [True, False])
    def test_get_users(
        self,
        service,
        db_session,
        h_userids,
        course_id,
        assignment_id,
        instructor_h_userid,
        assignment,
        student_in_assigment,
        teacher_in_assigment,
    ):
        factories.Assignment()
        course = factories.Course()
        factories.User(h_userid=student_in_assigment.h_userid)  # Duplicated student
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        db_session.flush()

        query_parameters = {}

        if instructor_h_userid:
            query_parameters["instructor_h_userid"] = teacher_in_assigment.h_userid

        if course_id:
            query_parameters["course_id"] = course.id

        if h_userids:
            query_parameters["h_userids"] = [student_in_assigment.h_userid]

        if assignment_id:
            query_parameters["assignment_id"] = assignment.id

        query = service.get_users(
            role_scope=RoleScope.COURSE, role_type=RoleType.LEARNER, **query_parameters
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
