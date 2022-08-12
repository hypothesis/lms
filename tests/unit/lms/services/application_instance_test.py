from unittest import mock

import pytest
from factory import Faker
from h_matchers import Any

from lms.models import LTIParams, ReusedConsumerKey
from lms.services import ApplicationInstanceNotFound
from lms.services.application_instance import ApplicationInstanceService, factory
from tests import factories


class TestApplicationInstanceService:
    def test_get_current(self, service, application_instance):
        assert service.get_current() == application_instance

    def test_get_current_raises_ApplicationInstanceNotFound_with_no_user(
        self, service, pyramid_request
    ):
        pyramid_request.lti_user = None

        with pytest.raises(ApplicationInstanceNotFound):
            service.get_current()

    def test_get_current_raises_for_non_existing_id(self, service, pyramid_request):
        pyramid_request.lti_user = pyramid_request.lti_user._replace(
            application_instance_id=1000
        )

        with pytest.raises(ApplicationInstanceNotFound):
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
            service.get_by_id(0)

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

            assert application_instance.developer_secret

        if developer_key:
            assert application_instance.developer_key == developer_key

        if lms_url:
            assert application_instance.lms_url == lms_url

        if deployment_id:
            assert application_instance.deployment_id == deployment_id

    @pytest.mark.parametrize("developer_key", ("key", None))
    @pytest.mark.parametrize("developer_secret", ("secret", None))
    def test_create_application_instance(
        self,
        service,
        aes_service,
        update_application_instance,
        developer_key,
        developer_secret,
    ):
        aes_service.build_iv.return_value = b"iv"
        aes_service.encrypt.return_value = b"secret"
        if not all([developer_secret, developer_key]):
            developer_key = developer_secret = None

        application_instance = service.create_application_instance(
            "https://example.com/",
            "example@example.com",
            developer_key,
            developer_secret,
            {},
        )

        assert application_instance.consumer_key
        assert application_instance.shared_secret
        assert application_instance.lms_url == "https://example.com/"
        assert application_instance.requesters_email == "example@example.com"
        assert application_instance.settings == {}
        update_application_instance.assert_called_once_with(
            application_instance,
            developer_key=developer_key,
            developer_secret=developer_secret,
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
    def test_update_from_lti_params(self, service, application_instance, field):
        lms_data = {field: field + "_value", "tool_consumer_instance_guid": "GUID"}

        service.update_from_lti_params(application_instance, LTIParams(lms_data))

        assert application_instance == Any.object.with_attrs(lms_data)

    def test_update_from_lti_params_no_guid_doesnt_change_values(
        self, service, application_instance
    ):
        service.update_from_lti_params(
            application_instance, LTIParams({"tool_consumer_instance_url": "NO EFFECT"})
        )

        assert application_instance.tool_consumer_instance_guid is None
        assert application_instance.tool_consumer_info_product_family_code is None

    def test_update_from_lti_params_existing_guid(self, service, application_instance):
        application_instance.tool_consumer_instance_guid = "EXISTING_GUID"

        with pytest.raises(ReusedConsumerKey):
            service.update_from_lti_params(
                application_instance,
                LTIParams({"tool_consumer_instance_guid": "NEW GUID"}),
            )

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
    def service(self, db_session, pyramid_request, aes_service):
        return ApplicationInstanceService(
            db=db_session, request=pyramid_request, aes_service=aes_service
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
    def test_it(self, ApplicationInstanceService, pyramid_request, aes_service):
        application_instance_service = factory(mock.sentinel.context, pyramid_request)

        ApplicationInstanceService.assert_called_once_with(
            pyramid_request.db, pyramid_request, aes_service
        )
        assert application_instance_service == ApplicationInstanceService.return_value

    @pytest.fixture(autouse=True)
    def ApplicationInstanceService(self, patch):
        return patch("lms.services.application_instance.ApplicationInstanceService")
