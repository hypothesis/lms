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

    def test_upsert_lms_user(self, service, lti_user, pyramid_request, db_session):
        user = service.upsert_user(lti_user)
        pyramid_request.lti_params["custom_canvas_user_id"] = "lms_api_user_id"

        lms_user = service.upsert_lms_user(user, pyramid_request.lti_params)

        lms_user = db_session.scalars(
            select(LMSUser).where(LMSUser.h_userid == user.h_userid)
        ).one()

        assert lms_user.display_name == user.display_name
        assert lms_user.email == user.email
        assert lms_user.updated == user.updated
        assert lms_user.lti_v13_user_id == pyramid_request.lti_params.v13.get("sub")
        assert lms_user.lms_api_user_id == "lms_api_user_id"

    def test_upsert_lms_user_doesnt_clear_lti_v13_user_id(
        self, service, lti_user, pyramid_request, db_session
    ):
        lms_user = factories.LMSUser(
            lti_v13_user_id="EXISTING",
            h_userid=lti_user.h_user.userid(authority="authority.example.com"),
        )
        db_session.commit()
        pyramid_request.lti_params.v13["sub"] = None

        user = service.upsert_user(lti_user)
        lms_user = service.upsert_lms_user(user, pyramid_request.lti_params)

        assert lms_user.lti_v13_user_id == "EXISTING"

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
        student_in_assignment,
    ):
        factories.User(h_userid=student_in_assignment.h_userid)  # Duplicated student

        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            admin_organization_ids=[organization.id],
        )

        assert [s.h_userid for s in db_session.scalars(query).all()] == [
            student_in_assignment.h_userid
        ]

    def test_get_users_by_h_userids(
        self,
        service,
        db_session,
        student_in_assignment,
        assignment,  # noqa: ARG002
        organization,
    ):
        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            h_userids=[student_in_assignment.h_userid],
            admin_organization_ids=[organization.id],
        )

        assert [s.h_userid for s in db_session.scalars(query).all()] == [
            student_in_assignment.h_userid
        ]

    @pytest.mark.usefixtures("assignment")
    def test_get_users_by_course_id(
        self, service, db_session, student_in_assignment, course, organization
    ):
        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            course_ids=[course.id],
            admin_organization_ids=[organization.id],
        )

        assert [s.h_userid for s in db_session.scalars(query).all()] == [
            student_in_assignment.h_userid
        ]

    @pytest.mark.usefixtures("assignment")
    @pytest.mark.parametrize("with_h_userids", [True, False])
    def test_get_users_for_course(
        self, service, db_session, student_in_assignment, course, with_h_userids
    ):
        query = service.get_users_for_course(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            lms_course=course.lms_course,
            h_userids=[student_in_assignment.h_userid] if with_h_userids else None,
        )

        assert [s.h_userid for s in db_session.scalars(query).all()] == [
            student_in_assignment.h_userid
        ]

    @pytest.mark.parametrize("with_h_userids", [True, False])
    def test_get_users_for_segments(
        self, service, db_session, course, with_h_userids, application_instance
    ):
        student = factories.User(application_instance=application_instance)
        lms_segment = factories.LMSSegment(lms_course=course.lms_course)
        lms_user = factories.LMSUser(
            lti_user_id=student.user_id, h_userid=student.h_userid
        )
        factories.LMSSegmentMembership.create(
            lms_segment=lms_segment,
            lms_user=lms_user,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )
        db_session.flush()

        query = service.get_users_for_segments(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            segment_ids=[lms_segment.id],
            h_userids=[student.h_userid] if with_h_userids else None,
        )

        assert [s.h_userid for s in db_session.scalars(query).all()] == [
            student.h_userid
        ]

    @pytest.mark.usefixtures("teacher_in_assigment")
    def test_get_users_by_assigment_id(
        self, service, db_session, student_in_assignment, assignment, organization
    ):
        factories.User(h_userid=student_in_assignment.h_userid)  # Duplicated student
        db_session.flush()

        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            assignment_ids=[assignment.id],
            admin_organization_ids=[organization.id],
        )

        assert [s.h_userid for s in db_session.scalars(query).all()] == [
            student_in_assignment.h_userid
        ]

    @pytest.mark.parametrize("with_h_userids", [True, False])
    def test_get_users_for_assignment(
        self, service, db_session, student_in_assignment, assignment, with_h_userids
    ):
        query = service.get_users_for_assignment(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            assignment_id=assignment.id,
            h_userids=[student_in_assignment.h_userid] if with_h_userids else None,
        )

        assert [s.h_userid for s in db_session.scalars(query).all()] == [
            student_in_assignment.h_userid
        ]

    @pytest.mark.usefixtures("assignment", "course")
    def test_get_users_by_instructor_h_userid(
        self, service, db_session, student_in_assignment, teacher_in_assigment
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

        assert [s.h_userid for s in db_session.scalars(query).all()] == [
            student_in_assignment.h_userid
        ]

    @pytest.mark.usefixtures("assignment", "course")
    @pytest.mark.parametrize("with_h_userids", [True, False])
    def test_get_users_for_organization(
        self,
        service,
        db_session,
        student_in_assignment,
        teacher_in_assigment,
        with_h_userids,
    ):
        query = service.get_users_for_organization(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            instructor_h_userid=teacher_in_assigment.h_userid,
            h_userids=[student_in_assignment.h_userid] if with_h_userids else None,
        )

        assert [s.h_userid for s in db_session.scalars(query).all()] == [
            student_in_assignment.h_userid
        ]

    @pytest.mark.usefixtures("teacher_in_assigment")
    def test_get_users_by_segment_authority_provided_id(
        self, service, db_session, student_in_assignment, assignment, organization
    ):
        factories.User(h_userid=student_in_assignment.h_userid)  # Duplicated student
        grouping = factories.CanvasSection()
        segment = factories.LMSSegment(
            h_authority_provided_id=grouping.authority_provided_id
        )
        factories.GroupingMembership(user=student_in_assignment, grouping=grouping)
        factories.LMSSegmentMembership(
            lms_user=student_in_assignment.lms_user,
            lms_segment=segment,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )

        db_session.flush()

        query = service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            assignment_ids=[assignment.id],
            admin_organization_ids=[organization.id],
            segment_authority_provided_ids=[grouping.authority_provided_id],
        )

        assert [s.h_userid for s in db_session.scalars(query).all()] == [
            student_in_assignment.h_userid
        ]

    @pytest.fixture
    def course(self, application_instance, db_session):
        course = factories.Course(application_instance=application_instance)
        lms_course = factories.LMSCourse(
            h_authority_provided_id=course.authority_provided_id
        )
        course.lms_course = lms_course
        db_session.flush()

        return course

    @pytest.fixture
    def assignment(self, course):
        assignment = factories.Assignment(course=course)
        factories.AssignmentGrouping(assignment=assignment, grouping=course)

        return assignment

    @pytest.fixture
    def student_in_assignment(self, assignment, application_instance, db_session):
        student = factories.User(application_instance=application_instance)
        lms_user = factories.LMSUser(
            lti_user_id=student.user_id, h_userid=student.h_userid
        )
        factories.AssignmentMembership.create(
            assignment=assignment,
            user=student,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )
        factories.GroupingMembership.create(
            grouping=assignment.course,
            user=student,
        )
        factories.LMSCourseMembership.create(
            lms_course=assignment.course.lms_course,
            lms_user=lms_user,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )
        factories.LMSUserAssignmentMembership.create(
            assignment=assignment,
            lms_user=lms_user,
            lti_role=factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER),
        )
        db_session.flush()

        return student

    @pytest.fixture
    def teacher_in_assigment(self, assignment):
        teacher = factories.User()
        factories.LMSUser(lti_user_id=teacher.user_id, h_userid=teacher.h_userid)
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
        factories.LMSUser(lti_user_id=user.user_id)
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
