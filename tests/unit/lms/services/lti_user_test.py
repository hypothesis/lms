from unittest.mock import sentinel

import pytest

from lms.services.lti_user import LTIUserService, factory


class TestLTIUserService:
    def test_from_lti_params(self, application_instance, lti_params, svc, display_name):
        lti_user = svc.from_lti_params(application_instance, lti_params)

        assert lti_user.user_id == lti_params["user_id"]
        assert lti_user.roles == lti_params["roles"]
        assert (
            lti_user.tool_consumer_instance_guid
            == lti_params["tool_consumer_instance_guid"]
        )
        assert lti_user.email == lti_params["lis_person_contact_email_primary"]
        assert lti_user.display_name == display_name(
            lti_params["lis_person_name_given"],
            lti_params["lis_person_name_family"],
            lti_params["lis_person_name_full"],
            lti_params["custom_display_name"],
        )
        assert lti_user.application_instance_id == application_instance.id

    def test_from_lti_params_without_name(
        self, application_instance, lti_params, svc, display_name
    ):
        del lti_params["lis_person_name_given"]
        del lti_params["lis_person_name_family"]
        del lti_params["lis_person_name_full"]
        del lti_params["custom_display_name"]

        lti_user = svc.from_lti_params(application_instance, lti_params)

        assert lti_user.display_name == display_name("", "", "", "")

    def test_serialize(self, svc, lti_user):
        assert svc.serialize(lti_user) == {
            "user_id": lti_user.user_id,
            "roles": lti_user.roles,
            "tool_consumer_instance_guid": lti_user.tool_consumer_instance_guid,
            "display_name": lti_user.display_name,
            "application_instance_id": lti_user.application_instance_id,
            "email": lti_user.email,
            "lti": {
                "course_id": lti_user.lti.course_id,
                "assignment_id": lti_user.lti.assignment_id,
            },
        }

    @pytest.fixture
    def lti_params(self):
        return {
            "user_id": "USER_ID",
            "roles": "ROLES",
            "tool_consumer_instance_guid": "TOOL_CONSUMER_INSTANCE_GUID",
            "lis_person_name_given": "LIS_PERSON_NAME_GIVEN",
            "lis_person_name_family": "LIS_PERSON_NAME_FAMILY",
            "lis_person_name_full": "LIS_PERSON_NAME_FULL",
            "lis_person_contact_email_primary": "LIS_PERSON_CONTACT_EMAIL_PRIMARY",
            "custom_display_name": "CUSTOM_DISPLAY_NAME",
            "context_id": "CONTEXT_ID",
            "resource_link_id": "RESOURCE_LINK_ID",
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
