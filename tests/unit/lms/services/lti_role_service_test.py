from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.models.lti_role import LTIRole, RoleScope, RoleType
from lms.services.lti_role_service import LTIRoleService, service_factory
from tests import factories


class TestLTIRoleService:
    def test_get_roles(self, svc, existing_roles):
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

    @pytest.fixture
    def svc(self, db_session):
        return LTIRoleService(db_session=db_session)

    @pytest.fixture
    def existing_roles(self):
        return factories.LTIRole.create_batch(3)


class TestServiceFactory:
    def test_it(self, pyramid_request, LTIRoleService):
        svc = service_factory(sentinel.context, pyramid_request)

        LTIRoleService.assert_called_once_with(db_session=pyramid_request.db)
        assert svc == LTIRoleService.return_value

    @pytest.fixture
    def LTIRoleService(self, patch):
        return patch("lms.services.lti_role_service.LTIRoleService")
