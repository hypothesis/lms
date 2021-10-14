from unittest import mock

import pytest

from lms.services import ApplicationInstanceNotFound
from lms.services.application_instance import ApplicationInstanceService, factory
from tests import factories


class TestApplicationInstanceService:
    def test_get_default(self, service, application_instance, pyramid_request):
        application_instance.consumer_key = pyramid_request.lti_user.oauth_consumer_key

        assert service.get_current() == application_instance

    def test_get_default_raises_ApplicationInstanceNotFound_with_no_user(
        self, service, pyramid_request
    ):
        pyramid_request.lti_user = None

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

    @pytest.fixture
    def service(self, db_session, pyramid_request):
        return ApplicationInstanceService(db=db_session, request=pyramid_request)

    @pytest.fixture(autouse=True)
    def application_instance(self):
        # Some noise
        factories.ApplicationInstance.create_batch(size=3)

        return factories.ApplicationInstance()


class TestFactory:
    def test_it(self, ApplicationInstanceService, pyramid_request):
        application_instance_service = factory(mock.sentinel.context, pyramid_request)

        ApplicationInstanceService.assert_called_once_with(
            pyramid_request.db, pyramid_request
        )
        assert application_instance_service == ApplicationInstanceService.return_value

    @pytest.fixture(autouse=True)
    def ApplicationInstanceService(self, patch):
        return patch("lms.services.application_instance.ApplicationInstanceService")
