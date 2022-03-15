from unittest import mock

import pytest

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
