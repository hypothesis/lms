import random
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.models.lti_role import LTIRole, LTIRoleOverride, RoleScope, RoleType
from lms.services.lti_role_service import LTIRoleService, Role, service_factory
from tests import factories


class TestLTIRoleService:
    @pytest.mark.parametrize("roles_as_string", [True, False])
    def test_get_roles(self, svc, existing_roles, roles_as_string):
        existing_role_strings = [role.value for role in existing_roles]
        new_roles = [
            "http://purl.imsglobal.org/vocab/lis/v2/system/person#SysSupport",
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Learner",
        ]

        role_descriptions = list(existing_role_strings)
        # Add one duplicate
        role_descriptions.append(existing_roles[0].value)
        role_descriptions.extend(new_roles)

        if roles_as_string:
            # pylint:  disable=redefined-variable-type
            role_descriptions = ", ".join(role_descriptions)
        roles = svc.get_roles(role_descriptions)

        expected_new_roles = [
            Any.instance_of(LTIRole).with_attrs({"value": value}) for value in new_roles
        ]
        assert roles == Any.list.containing(existing_roles + expected_new_roles).only()

    def test_get_roles_with_existing_only(self, svc, existing_roles):
        # This is to get some coverage over the branch where we don't create
        # any new rows
        roles = svc.get_roles(", ".join([role.value for role in existing_roles]))

        assert roles == existing_roles

    def test_get_roles_updates_value(self, svc):
        # Create a role where the type and scope don't match the value
        factories.LTIRole(
            _value="Instructor", type=RoleType.ADMIN, scope=RoleScope.SYSTEM
        )

        roles = svc.get_roles("Instructor")

        assert len(roles) == 1
        assert roles[0].type == RoleType.INSTRUCTOR
        assert roles[0].scope == RoleScope.COURSE

    def test_get_roles_for_application_instance_no_overrides(
        self, svc, existing_roles, application_instance
    ):
        roles = svc.get_roles_for_application_instance(
            application_instance, existing_roles
        )

        assert roles == [
            Role(scope=role.scope, type=role.type, value=role.value)
            for role in existing_roles
        ]

    def test_get_roles_for_application_instance_with_overrides(
        self, svc, existing_roles, application_instance, db_session
    ):
        override = LTIRoleOverride(
            lti_role=existing_roles[0],
            application_instance=application_instance,
            # Make sure the override has different values
            scope=self.random_enum_excluding(RoleScope, existing_roles[0].scope),
            type=self.random_enum_excluding(RoleType, existing_roles[0].type),
        )
        db_session.add(override)

        roles = svc.get_roles_for_application_instance(
            application_instance, existing_roles
        )

        assert override.scope == roles[0].scope
        assert override.type == roles[0].type
        assert roles[1:] == [
            Role(scope=role.scope, type=role.type, value=role.value)
            for role in existing_roles[1:]
        ]

    def test_search(self, existing_roles, svc):
        results = svc.search()

        assert results.all() == existing_roles

    def test_search_by_id(self, existing_roles, svc, db_session):
        db_session.flush()  # Give all roles IDs

        results = svc.search(id_=existing_roles[0].id)

        assert results.one() == existing_roles[0]

    def test_search_override(self, existing_overrides, svc):
        results = svc.search_override()

        assert results.all() == existing_overrides

    def test_search_override_by_id(self, existing_overrides, svc, db_session):
        db_session.flush()  # Give all roles IDs

        results = svc.search_override(id_=existing_overrides[0].id)

        assert results.one() == existing_overrides[0]

    def test_new_role_override(
        self, svc, application_instance, existing_roles, db_session
    ):
        override = svc.new_role_override(
            application_instance,
            existing_roles[0],
            type_=RoleType.INSTRUCTOR,
            scope=RoleScope.SYSTEM,
        )
        db_session.commit()

        assert svc.search_override(id_=override.id).one() == override
        assert override.type == RoleType.INSTRUCTOR
        assert override.scope == RoleScope.SYSTEM

    def test_delete_override(self, existing_overrides, svc, db_session):
        db_session.flush()  # Give all roles IDs
        id_ = existing_overrides[0].id

        svc.delete_override(existing_overrides[0])

        assert not svc.search_override(id_=id_).all()

    def test_update_override(self, existing_overrides, svc, db_session):
        db_session.flush()  # Give all roles IDs

        override = svc.update_override(
            existing_overrides[0], scope=RoleScope.COURSE, type_=RoleType.INSTRUCTOR
        )

        assert override.scope == RoleScope.COURSE
        assert override.type == RoleType.INSTRUCTOR

    @pytest.fixture
    def svc(self, db_session):
        return LTIRoleService(db_session=db_session)

    @pytest.fixture
    def existing_roles(self):
        return sorted(factories.LTIRole.create_batch(3), key=lambda x: x.value)

    @pytest.fixture
    def existing_overrides(self, existing_roles, application_instance):
        return [
            factories.LTIRoleOverride(
                lti_role=role, application_instance=application_instance
            )
            for role in existing_roles
        ]

    @staticmethod
    def random_enum_excluding(enum_, excluding):
        return random.choice(list(set(enum_) - {excluding}))


class TestServiceFactory:
    def test_it(self, pyramid_request, LTIRoleService):
        svc = service_factory(sentinel.context, pyramid_request)

        LTIRoleService.assert_called_once_with(db_session=pyramid_request.db)
        assert svc == LTIRoleService.return_value

    @pytest.fixture
    def LTIRoleService(self, patch):
        return patch("lms.services.lti_role_service.LTIRoleService")
