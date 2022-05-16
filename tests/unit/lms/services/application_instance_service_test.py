from unittest import mock

import pytest
from factory import Faker

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

    @pytest.mark.parametrize(
        "developer_secret,developer_key",
        [
            ("TEST_DEVELOPER_SECRET", "DEVELOPER_KEY"),
            ("TEST_DEVELOPER_SECRET", None),
            (None, "DEVELOPER_KEY"),
            (None, None),
        ],
    )
    def test_build_from_lms_url(self, developer_secret, developer_key, service):
        application_instance = service.build_from_lms_url(
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
        assert application_instance.developer_key == developer_key
        assert application_instance.settings == {}
        if developer_secret:
            assert application_instance.developer_secret

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
