from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.models.lti_role import LTIRole, RoleScope, RoleType
from lms.services.lti_role_service import LTIRoleService, service_factory
from tests import factories


class TestGetRoles:
    def test_it(self, svc, existing_roles):
        existing_role_strings = [role.value for role in existing_roles]
        new_roles = [
            "http://purl.imsglobal.org/vocab/lis/v2/system/person#SysSupport",
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Learner",
        ]

        role_descriptions = list(existing_role_strings)
        # Add one duplicate
        role_descriptions.append(existing_roles[0].value)
        role_descriptions.extend(new_roles)

        roles = svc.get_roles(", ".join(role_descriptions))

        expected_new_roles = [
            Any.instance_of(LTIRole).with_attrs({"value": value}) for value in new_roles
        ]
        assert roles == Any.list.containing(existing_roles + expected_new_roles).only()

    def test_it_with_existing_only(self, svc, existing_roles):
        # This is to get some coverage over the branch where we don't create
        # any new rows
        roles = svc.get_roles(", ".join([role.value for role in existing_roles]))

        assert roles == existing_roles

    def test_it_updates_value(self, svc):
        # Create a role where the type and scope don't match the value
        factories.LTIRole(
            _value="Instructor", type=RoleType.ADMIN, scope=RoleScope.SYSTEM
        )

        roles = svc.get_roles("Instructor")

        assert len(roles) == 1
        assert roles[0].type == RoleType.INSTRUCTOR
        assert roles[0].scope == RoleScope.COURSE

    @pytest.fixture
    def existing_roles(self):
        return factories.LTIRole.create_batch(3)


class TestGetUsers:
    def test_it_returns_an_empty_list_if_there_are_no_matching_users(self, svc):
        assert not list(svc.get_users("instructor"))

    def test_it_returns_matching_users(self, svc, instructors):
        assert (
            svc.get_users("instructor") == Any.iterable.containing(instructors).only()
        )

    def test_it_doesnt_return_users_who_dont_have_a_matching_role(self, svc):
        application_instance = factories.ApplicationInstance()
        learner = factories.User(application_instance=application_instance)
        # Make the user a learner in an assignment that belongs to a course
        # that belongs to the application instance.
        course = factories.Course(application_instance=application_instance)
        assignment = factories.Assignment()
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        learner_role = factories.LTIRole(value="Learner")
        factories.AssignmentMembership(
            assignment=assignment, user=learner, lti_role=learner_role
        )

        assert learner not in list(svc.get_users("instructor"))

    def test_it_doesnt_return_users_from_other_application_instances(
        self, svc, application_instances, instructor_role
    ):
        other_application_instance = factories.ApplicationInstance()
        other_instructor = factories.User(
            application_instance=other_application_instance
        )
        # Make the user an instructor in an assignment that belongs to a course
        # that belongs to another application instance.
        course = factories.Course(application_instance=other_application_instance)
        assignment = factories.Assignment()
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        factories.AssignmentMembership(
            assignment=assignment, user=other_instructor, lti_role=instructor_role
        )

        assert other_instructor not in list(
            svc.get_users("instructor", application_instances=application_instances)
        )

    @pytest.fixture
    def application_instances(self, db_session):
        """Return the application instances that the instructors will belong to."""
        application_instances = factories.ApplicationInstance.create_batch(size=2)
        db_session.flush()  # Generate application instance IDs.
        return application_instances

    @pytest.fixture
    def instructor_role(self):
        return factories.LTIRole(value="Instructor")

    @pytest.fixture
    def instructors(self, application_instances, instructor_role):
        instructors = []

        for application_instance in application_instances:
            instructor = factories.User(application_instance=application_instance)
            # Make the user an instructor in an assignment that belongs to a
            # course that belongs to the application instance.
            course = factories.Course(application_instance=application_instance)
            assignment = factories.Assignment()
            factories.AssignmentGrouping(assignment=assignment, grouping=course)
            factories.AssignmentMembership(
                assignment=assignment, user=instructor, lti_role=instructor_role
            )
            instructors.append(instructor)

        return instructors


class TestServiceFactory:
    def test_it(self, pyramid_request, LTIRoleService):
        svc = service_factory(sentinel.context, pyramid_request)

        LTIRoleService.assert_called_once_with(db_session=pyramid_request.db)
        assert svc == LTIRoleService.return_value

    @pytest.fixture
    def LTIRoleService(self, patch):
        return patch("lms.services.lti_role_service.LTIRoleService")


@pytest.fixture
def svc(db_session):
    return LTIRoleService(db_session=db_session)
