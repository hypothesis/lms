from unittest.mock import sentinel

import pytest
from sqlalchemy.exc import IntegrityError

from lms.views.admin.lti_registration import AdminLTIRegistrationViews
from tests import factories
from tests.matchers import Any, temporary_redirect_to


@pytest.mark.usefixtures(
    "pyramid_config", "application_instance_service", "lti_registration_service"
)
class TestAdminApplicationInstanceViews:
    def test_registrations(self, views):
        assert views.registrations() == {}

    def test_new_registration(self, views):
        assert views.new_registration() == {}

    @pytest.mark.usefixtures("with_form_submission")
    def test_new_registration_callback(
        self, views, lti_registration_service, pyramid_request
    ):
        response = views.new_registration_callback()

        lti_registration_service.create_registration.assert_called_once_with(
            issuer="ISSUER",
            client_id="CLIENT_ID",
            auth_login_url="AUTH_LOGIN_URL",
            key_set_url="KEY_SET_URL",
            token_url="TOKEN_URL",
        )

        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.registration.id",
                id_=lti_registration_service.create_registration.return_value.id,
            )
        )

    @pytest.mark.usefixtures("with_form_submission")
    def test_new_registration_callback_duplicate(self, lti_registration_service, views):
        lti_registration_service.create_registration.side_effect = IntegrityError(
            Any(), Any(), Any()
        )

        response = views.new_registration_callback()

        assert response.status_code == 400

    @pytest.mark.usefixtures("with_form_submission")
    @pytest.mark.parametrize(
        "missing", ["issuer", "client_id", "auth_login_url", "key_set_url", "token_url"]
    )
    def test_new_registration_callback_missing_params(
        self, pyramid_request, missing, views
    ):
        del pyramid_request.params[missing]

        response = views.new_registration_callback()

        assert response.status_code == 400

    def test_search_not_query(self, pyramid_request):
        response = AdminLTIRegistrationViews(pyramid_request).search()

        assert pyramid_request.session.peek_flash("errors")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.registrations")
        )

    def test_search_single_result(
        self, pyramid_request, lti_registration_service, lti_registration, views
    ):
        lti_registration_service.search_registrations.return_value = [lti_registration]
        pyramid_request.params["issuer"] = sentinel.issuer

        response = views.search()

        lti_registration_service.search_registrations.assert_called_once_with(
            issuer=sentinel.issuer, client_id=None
        )
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.registration.id",
                id_=lti_registration_service.search_registrations.return_value[0].id,
            )
        )

    def test_search_multiple_results(
        self, pyramid_request, lti_registration_service, views
    ):
        pyramid_request.params = {
            "issuer": sentinel.issuer,
            "client_id": sentinel.client_id,
        }

        response = views.search()

        lti_registration_service.search_registrations.assert_called_once_with(
            issuer=sentinel.issuer, client_id=sentinel.client_id
        )

        assert response == {
            "registrations": lti_registration_service.search_registrations.return_value
        }

    def test_show_registration(self, pyramid_request, lti_registration_service, views):
        pyramid_request.matchdict["id_"] = sentinel.id_

        response = views.show_registration()

        lti_registration_service.get_by_id.assert_called_once_with(sentinel.id_)
        assert (
            response["registration"] == lti_registration_service.get_by_id.return_value
        )

    def test_registration_new_instance(
        self, pyramid_request, lti_registration_service, views
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_

        response = views.registration_new_instance()

        lti_registration_service.get_by_id.assert_called_once_with(sentinel.id_)
        assert (
            response["lti_registration"]
            == lti_registration_service.get_by_id.return_value
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {}
        return pyramid_request

    @pytest.fixture
    def with_form_submission(self, pyramid_request):
        pyramid_request.params["issuer"] = "ISSUER"
        pyramid_request.params["client_id"] = "CLIENT_ID"
        pyramid_request.params["auth_login_url"] = "AUTH_LOGIN_URL"
        pyramid_request.params["key_set_url"] = "KEY_SET_URL"
        pyramid_request.params["token_url"] = "TOKEN_URL"

        return pyramid_request

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminLTIRegistrationViews(pyramid_request)

    @pytest.fixture
    def lti_registration(self):
        return factories.LTIRegistration()
