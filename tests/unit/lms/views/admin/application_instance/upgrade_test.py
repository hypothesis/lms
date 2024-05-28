import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPClientError, HTTPFound

from lms.models import ApplicationInstance
from lms.services import ApplicationInstanceNotFound
from lms.views.admin.application_instance.upgrade import UpgradeApplicationInstanceViews
from tests import factories
from tests.matchers import temporary_redirect_to

REDIRECT_TO_UPGRADE_AI = Any.instance_of(HTTPFound).with_attrs(
    {"location": Any.string.containing("/admin/instances/upgrade")}
)


@pytest.mark.usefixtures("application_instance_service", "lti_registration_service")
class TestUpgradeApplicationInstanceViews:
    @pytest.mark.parametrize("lti_registration_id", ("123", "  123   "))
    def test_upgrade_instance_start(
        self, views, pyramid_request, lti_registration_service, lti_registration_id
    ):
        pyramid_request.params = {
            "lti_registration_id": lti_registration_id,
            "key_1": "value_1",
            "key_2": "value_2",
        }

        response = views.upgrade_instance_start()

        lti_registration_service.get_by_id.assert_called_once_with("123")
        assert response == dict(
            pyramid_request.params,
            lti_registration=lti_registration_service.get_by_id.return_value,
        )

    def test_upgrade_instance_start_with_no_registration_id(
        self, views, pyramid_request
    ):
        pyramid_request.params.pop("lti_registration_id", None)

        with pytest.raises(HTTPClientError):
            views.upgrade_instance_start()

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_instance_callback(
        self,
        views,
        pyramid_request,
        application_instance,
        application_instance_service,
        lti_registration_service,
    ):
        lti_registration = factories.LTIRegistration()
        lti_registration_service.get_by_id.return_value = lti_registration
        assert not application_instance.lti_registration

        response = views.upgrade_instance_callback()

        application_instance_service.get_by_consumer_key.assert_called_once_with(
            application_instance.consumer_key
        )
        assert application_instance.lti_registration == lti_registration
        assert (
            application_instance.deployment_id
            == pyramid_request.params["deployment_id"]
        )
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance", id_=application_instance.id)
        )

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_instance_callback_with_no_deployment_id(
        self, views, pyramid_request
    ):
        del pyramid_request.POST["deployment_id"]

        assert views.upgrade_instance_callback() == REDIRECT_TO_UPGRADE_AI

    @pytest.mark.usefixtures("with_upgrade_form", "lti_v13_application_instance")
    def test_upgrade_instance_callback_already_upgraded(self, views):
        assert views.upgrade_instance_callback() == REDIRECT_TO_UPGRADE_AI

    @pytest.mark.filterwarnings(
        "ignore:transaction already deassociated from connection"
    )
    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_instance_callback_with_duplicate(
        self, views, db_session, lti_registration_service
    ):
        lti_registration = factories.LTIRegistration()
        lti_registration_service.get_by_id.return_value = lti_registration
        factories.ApplicationInstance(
            lti_registration=lti_registration, deployment_id="DEPLOYMENT_ID"
        )

        response = views.upgrade_instance_callback()

        assert response == REDIRECT_TO_UPGRADE_AI

        # Show that the DB connection has not been permanently broken. This
        # would cause us to fail completely when trying to present the error.
        # We are checking we do _not_ raise `PendingRollbackError` here.
        db_session.query(ApplicationInstance).all()

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_instance_callback_with_non_existent_instance(
        self, views, application_instance_service
    ):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )

        assert views.upgrade_instance_callback() == REDIRECT_TO_UPGRADE_AI

    @pytest.fixture
    def with_upgrade_form(self, pyramid_request, application_instance):
        pyramid_request.POST = pyramid_request.params = {
            "name": "NAME",
            "lms_url": "http://lms-url.com",
            "email": "test@email.com",
            "deployment_id": "DEPLOYMENT_ID",
            "consumer_key": application_instance.consumer_key,
        }

        return pyramid_request

    @pytest.fixture
    def views(self, pyramid_request):
        return UpgradeApplicationInstanceViews(pyramid_request)
