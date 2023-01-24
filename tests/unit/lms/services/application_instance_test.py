from unittest import mock

import pytest
from factory import Faker
from h_matchers import Any

from lms.models import LTIParams, ReusedConsumerKey
from lms.services import ApplicationInstanceNotFound
from lms.services.application_instance import (
    AccountDisabled,
    ApplicationInstanceService,
    factory,
)
from lms.validation import ValidationError
from tests import factories


class TestApplicationInstanceService:
    @pytest.mark.parametrize("has_org", (True, False))
    def test_get_current(self, service, application_instance, has_org):
        if has_org:
            application_instance.organization = factories.Organization(enabled=True)

        assert service.get_current() == application_instance

    def test_get_current_raises_ApplicationInstanceNotFound_with_no_user(
        self, service, pyramid_request
    ):
        pyramid_request.lti_user = None

        with pytest.raises(ApplicationInstanceNotFound):
            service.get_current()

    def test_get_current_raises_for_non_existing_id(self, service, pyramid_request):
        pyramid_request.lti_user.application_instance_id = 1000

        with pytest.raises(ApplicationInstanceNotFound):
            service.get_current()

    def test_get_current_raises_for_disabled_organisations(
        self, service, application_instance
    ):
        application_instance.organization = factories.Organization(enabled=False)

        with pytest.raises(AccountDisabled):
            service.get_current()

    def test_get_by_consumer_key(self, service, application_instance):
        assert (
            service.get_by_consumer_key(application_instance.consumer_key)
            == application_instance
        )

    @pytest.mark.parametrize("consumer_key", ("MISSING", None))
    def test_get_by_consumer_key_raises_on_missing(self, service, consumer_key):
        with pytest.raises(ApplicationInstanceNotFound):
            service.get_by_consumer_key(consumer_key)

    def test_get_by_id(self, service, application_instance):
        assert service.get_by_id(application_instance.id) == application_instance

    def test_get_by_not_found(self, service):
        with pytest.raises(ApplicationInstanceNotFound):
            service.get_by_id(100_000_000)

    def test_get_by_deployment_id(
        self,
        service,
        lti_v13_application_instance,
    ):
        assert (
            service.get_by_deployment_id(
                lti_v13_application_instance.lti_registration.issuer,
                lti_v13_application_instance.lti_registration.client_id,
                lti_v13_application_instance.deployment_id,
            )
            == lti_v13_application_instance
        )

    @pytest.mark.parametrize(
        "issuer,client_id,deployment_id",
        [
            (None, "MISSING", "MISSING"),
            ("MISSING", None, "MISSING"),
            ("MISSING", "MISSING", None),
            ("MISSING", "MISSING", "MISSING"),
        ],
    )
    def test_get_by_deployment_id_raises_on_missing(
        self, service, issuer, client_id, deployment_id
    ):
        with pytest.raises(ApplicationInstanceNotFound):
            service.get_by_deployment_id(issuer, client_id, deployment_id)

    @pytest.mark.parametrize("lms_url", (None, "http://lms-url.com"))
    @pytest.mark.parametrize("deployment_id", (None, "DEPLOYMENT_ID"))
    @pytest.mark.parametrize("developer_key", (None, "KEY"))
    @pytest.mark.parametrize("developer_secret", (None, "SECRET"))
    def test_update_application_instance(
        self,
        service,
        application_instance,
        lms_url,
        deployment_id,
        developer_key,
        developer_secret,
        aes_service,
    ):
        service.update_application_instance(
            application_instance,
            lms_url=lms_url,
            deployment_id=deployment_id,
            developer_key=developer_key,
            developer_secret=developer_secret,
        )

        if developer_secret:
            aes_service.build_iv.assert_called_once()
            aes_service.encrypt.assert_called_once_with(
                aes_service.build_iv.return_value, developer_secret
            )

            assert (
                application_instance.aes_cipher_iv == aes_service.build_iv.return_value
            )
            assert (
                application_instance.developer_secret
                == aes_service.encrypt.return_value
            )

        if developer_key:
            assert application_instance.developer_key == developer_key

        if lms_url:
            assert application_instance.lms_url == lms_url

        if deployment_id:
            assert application_instance.deployment_id == deployment_id

    def test_update_application_instance_with_invalid_org_id(
        self, organization_service, application_instance, service
    ):
        organization_service.get_by_public_id.return_value = None

        with pytest.raises(ValidationError):
            service.update_application_instance(
                application_instance, organization_public_id=mock.sentinel.org_id
            )

        organization_service.get_by_public_id.assert_called_once_with(
            mock.sentinel.org_id
        )

    def test_update_application_instance_with_org_id(
        self, organization_service, application_instance, service
    ):
        org = factories.Organization()
        organization_service.get_by_public_id.return_value = org

        service.update_application_instance(
            application_instance, organization_public_id=mock.sentinel.org_id
        )

        organization_service.get_by_public_id.assert_called_once_with(
            mock.sentinel.org_id
        )
        assert application_instance.organization == org

    @pytest.mark.parametrize("developer_key", ("key", None))
    @pytest.mark.parametrize("developer_secret", ("secret", None))
    @pytest.mark.parametrize("organization_public_id", ("us.lms.org.ID", None))
    def test_create_application_instance(
        self,
        service,
        update_application_instance,
        developer_key,
        developer_secret,
        organization_public_id,
    ):
        application_instance = service.create_application_instance(
            lms_url="https://example.com/",
            email="example@example.com",
            developer_key=developer_key,
            developer_secret=developer_secret,
            organization_public_id=organization_public_id,
        )

        # Things we set ourselves
        assert application_instance.shared_secret == Any.string.matching("[0-9a-f]{32}")
        assert application_instance.consumer_key == Any.string.matching(
            "Hypothesis[0-9a-f]{16}"
        )
        assert application_instance.lms_url == "https://example.com/"
        assert application_instance.requesters_email == "example@example.com"
        assert application_instance.settings == {
            "canvas": {
                "sections_enabled": False,
                "groups_enabled": bool(developer_key),
            }
        }

        # Things we delegate to `update_application_instance`
        if not all([developer_secret, developer_key]):
            developer_key = developer_secret = None

        update_application_instance.assert_called_once_with(
            application_instance,
            developer_key=developer_key,
            developer_secret=developer_secret,
            organization_public_id=organization_public_id,
        )

    @pytest.mark.parametrize("field", ["issuer", "client_id"])
    def test_search_by_registration_fields(
        self, field, service, with_application_instances_for_search
    ):
        registrations, _ = with_application_instances_for_search

        for registration in registrations:
            instances = service.search(**{field: getattr(registration, field)})

            assert len(instances) == 5
            assert {getattr(registration, field)} == {
                *[getattr(instance.lti_registration, field) for instance in instances]
            }

    @pytest.mark.parametrize(
        "field", ["consumer_key", "deployment_id", "tool_consumer_instance_guid"]
    )
    def test_search_by_instance_fields(
        self, field, service, with_application_instances_for_search
    ):
        _, instances = with_application_instances_for_search

        for instance in instances:
            found_instances = service.search(**{field: getattr(instance, field)})
            assert len(found_instances) == 1
            assert getattr(instance, field) == getattr(found_instances[0], field)

    @pytest.mark.parametrize(
        "field",
        (
            "tool_consumer_info_product_family_code",
            "tool_consumer_instance_description",
            "tool_consumer_instance_url",
            "tool_consumer_instance_name",
            "tool_consumer_instance_contact_email",
            "tool_consumer_info_version",
            "custom_canvas_api_domain",
        ),
    )
    def test_update_from_lti_params(
        self, service, organization_service, application_instance, field
    ):
        lms_data = {field: field + "_value", "tool_consumer_instance_guid": "GUID"}

        service.update_from_lti_params(application_instance, LTIParams(lms_data))

        organization_service.auto_assign_organization.assert_called_once_with(
            application_instance
        )
        assert application_instance == Any.object.with_attrs(lms_data)

    def test_update_from_lti_params_no_guid_doesnt_change_values(
        self, service, organization_service, application_instance
    ):
        service.update_from_lti_params(
            application_instance, LTIParams({"tool_consumer_instance_url": "NO EFFECT"})
        )

        organization_service.auto_assign_organization.assert_not_called()
        assert application_instance.tool_consumer_instance_guid is None
        assert application_instance.tool_consumer_info_product_family_code is None

    def test_update_from_lti_params_existing_guid(
        self, service, organization_service, application_instance
    ):
        application_instance.tool_consumer_instance_guid = "EXISTING_GUID"

        with pytest.raises(ReusedConsumerKey):
            service.update_from_lti_params(
                application_instance,
                LTIParams({"tool_consumer_instance_guid": "NEW GUID"}),
            )

        organization_service.auto_assign_organization.assert_not_called()
        assert application_instance.tool_consumer_instance_guid == "EXISTING_GUID"

    @pytest.fixture
    def with_application_instances_for_search(self):
        registrations = factories.LTIRegistration.create_batch(size=3)
        instances = []

        for registration in registrations:
            instances.extend(
                factories.ApplicationInstance.create_batch(
                    size=5,
                    lti_registration=registration,
                    tool_consumer_instance_guid=Faker("hexify", text="^" * 32),
                    deployment_id=Faker("hexify", text="^" * 8),
                )
            )

        return registrations, instances

    @pytest.fixture
    def service(self, db_session, pyramid_request, aes_service, organization_service):
        return ApplicationInstanceService(
            db=db_session,
            request=pyramid_request,
            aes_service=aes_service,
            organization_service=organization_service,
        )

    @pytest.fixture
    def update_application_instance(self, service):
        with mock.patch.object(
            service, "update_application_instance"
        ) as update_application_instance:
            yield update_application_instance

    @pytest.fixture(autouse=True)
    def with_application_instance_noise(self):
        factories.ApplicationInstance.create_batch(size=3)


class TestFactory:
    def test_it(
        self,
        ApplicationInstanceService,
        pyramid_request,
        aes_service,
        organization_service,
    ):
        application_instance_service = factory(mock.sentinel.context, pyramid_request)

        ApplicationInstanceService.assert_called_once_with(
            db=pyramid_request.db,
            request=pyramid_request,
            aes_service=aes_service,
            organization_service=organization_service,
        )
        assert application_instance_service == ApplicationInstanceService.return_value

    @pytest.fixture(autouse=True)
    def ApplicationInstanceService(self, patch):
        return patch("lms.services.application_instance.ApplicationInstanceService")
