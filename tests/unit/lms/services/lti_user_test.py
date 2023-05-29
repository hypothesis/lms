from unittest.mock import sentinel

import pytest

from lms.services.lti_user import LTIUserService, factory


class TestLTIUserService:
    def test_from_auth_params(
        self,
        application_instance,
        auth_params,
        svc,
        display_name,
        application_instance_service,
    ):
        lti_user = svc.from_auth_params(application_instance, auth_params)

        assert lti_user.user_id == auth_params["user_id"]
        assert lti_user.roles == auth_params["roles"]
        assert (
            lti_user.tool_consumer_instance_guid
            == auth_params["tool_consumer_instance_guid"]
        )
        assert lti_user.email == auth_params["lis_person_contact_email_primary"]
        assert lti_user.display_name == display_name(
            auth_params["lis_person_name_given"],
            auth_params["lis_person_name_family"],
            auth_params["lis_person_name_full"],
        )
        assert (
            lti_user.application_instance.id
            == application_instance_service.get_for_launch.return_value.id
        )

    def test_serialize(self, svc, lti_user):
        assert svc.serialize(lti_user) == {
            "user_id": lti_user.user_id,
            "roles": lti_user.roles,
            "tool_consumer_instance_guid": lti_user.tool_consumer_instance_guid,
            "display_name": lti_user.display_name,
            "application_instance_id": lti_user.application_instance.id,
            "email": lti_user.email,
        }

    @pytest.fixture
    def auth_params(self):
        return {
            "user_id": "USER_ID",
            "roles": "ROLES",
            "tool_consumer_instance_guid": "TOOL_CONSUMER_INSTANCE_GUID",
            "lis_person_name_given": "LIS_PERSON_NAME_GIVEN",
            "lis_person_name_family": "LIS_PERSON_NAME_FAMILY",
            "lis_person_name_full": "LIS_PERSON_NAME_FULL",
            "lis_person_contact_email_primary": "LIS_PERSON_CONTACT_EMAIL_PRIMARY",
        }

    @pytest.fixture
    def svc(self, lti_role_service, application_instance_service):
        return LTIUserService(lti_role_service, application_instance_service)

    @pytest.fixture
    def display_name(self, patch):
        return patch("lms.services.lti_user.display_name")


class TestFactory:
    @pytest.mark.usefixtures("lti_role_service", "application_instance_service")
    def test_it(self, pyramid_request):
        svc = factory(sentinel.context, pyramid_request)

        assert isinstance(svc, LTIUserService)
