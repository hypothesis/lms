from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound
from sqlalchemy.exc import IntegrityError

from lms.views.admin.lti_registration import AdminLTIRegistrationViews
from tests.matchers import Any, temporary_redirect_to


@pytest.mark.usefixtures(
    "pyramid_config", "application_instance_service", "lti_registration_service"
)
class TestAdminApplicationInstanceViews:
    def test_registrations(self, views):
        assert views.registrations() == {}

    def test_new_registration(self, views):
        assert views.new_registration() == {}

    @pytest.mark.parametrize(
        "issuer,client_id,expected",
        [
            (
                "https://blackboard.com",
                "CLIENT_ID",
                {
                    "auth_login_url": "https://developer.blackboard.com/api/v1/gateway/oidcauth",
                    "key_set_url": "https://developer.blackboard.com/api/v1/management/applications/CLIENT_ID/jwks.json",
                    "token_url": "https://developer.blackboard.com/api/v1/gateway/oauth2/jwttoken",
                },
            ),
            (
                "https://hypothesis.instructure.com",
                "client_id",
                {
                    "auth_login_url": "https://sso.canvaslms.com/api/lti/authorize_redirect",
                    "key_set_url": "https://sso.canvaslms.com/api/lti/security/jwks",
                    "token_url": "https://sso.canvaslms.com/login/oauth2/token",
                },
            ),
            (
                "https://hypothesis.brightspace.com",
                "client_id",
                {
                    "auth_login_url": "https://hypothesis.brightspace.com/d2l/lti/authenticate",
                    "key_set_url": "https://hypothesis.brightspace.com/d2l/.well-known/jwks",
                    "token_url": "https://hypothesis.brightspace.com/core/connect/token",
                },
            ),
            (
                "https://hypothesis.moodlecloud.com",
                "client_id",
                {
                    "auth_login_url": "https://hypothesis.moodlecloud.com/mod/lti/auth.php",
                    "key_set_url": "https://hypothesis.moodlecloud.com/mod/lti/certs.php",
                    "token_url": "https://hypothesis.moodlecloud.com/mod/lti/token.php",
                },
            ),
            (
                "https://unknown.lms.com",
                "client_id",
                {"auth_login_url": None, "key_set_url": None, "token_url": None},
            ),
        ],
    )
    @pytest.mark.usefixtures("with_form_submission")
    def test_suggest_lms_urls(
        self, views, pyramid_request, issuer, client_id, expected
    ):
        pyramid_request.params["issuer"] = issuer
        pyramid_request.params["client_id"] = client_id

        response = views.suggest_lms_urls()

        assert response == expected

    def test_suggest_lms_urls_failed_validation(self, views):
        assert not views.suggest_lms_urls()

    @pytest.mark.usefixtures("with_form_submission")
    def test_new_registration_callback(
        self, views, lti_registration_service, pyramid_request
    ):
        response = views.new_registration_callback()

        lti_registration_service.create_registration.assert_called_once_with(
            issuer="http://issuer.com",
            client_id="CLIENT_ID",
            auth_login_url="http://auth-login-url.com",
            key_set_url="http://key-set-url.com",
            token_url="http://token-url.com",
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
        del pyramid_request.POST[missing]

        response = views.new_registration_callback()

        assert response.status_code == 400

    @pytest.mark.usefixtures("with_form_submission")
    def test_new_registration_bad_issuer(self, pyramid_request, views):
        pyramid_request.POST["issuer"] = "https://issuer.com/"

        response = views.new_registration_callback()

        assert response.status_code == 400

    def test_search(self, pyramid_request, lti_registration_service, views):
        pyramid_request.POST = pyramid_request.params = {
            "id": "1",
            "issuer": "ISSUER",
            "client_id": "CLIENT_ID",
        }

        response = views.search()

        lti_registration_service.search_registrations.assert_called_once_with(
            id_="1", issuer="ISSUER", client_id="CLIENT_ID"
        )

        assert response == {
            "registrations": lti_registration_service.search_registrations.return_value
        }

    def test_search_invalid(self, pyramid_request, views):
        pyramid_request.POST["id"] = "not a number"

        assert not views.search()
        assert pyramid_request.session.peek_flash

    def test_show_registration(self, pyramid_request, lti_registration_service, views):
        pyramid_request.matchdict["id_"] = sentinel.id_

        response = views.show_registration()

        lti_registration_service.get_by_id.assert_called_once_with(sentinel.id_)
        assert (
            response["registration"] == lti_registration_service.get_by_id.return_value
        )

    def test_show_registration_404(
        self, pyramid_request, lti_registration_service, views
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_
        lti_registration_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            views.show_registration()

    @pytest.mark.usefixtures("with_form_submission")
    def test_update_registration(
        self, pyramid_request, lti_registration_service, views
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_

        response = views.update_registration()

        lti_registration_service.get_by_id.assert_called_once_with(sentinel.id_)
        assert (
            response["registration"] == lti_registration_service.get_by_id.return_value
        )
        assert pyramid_request.session.peek_flash("messages")

    @pytest.mark.usefixtures("with_form_submission")
    def test_update_registration_failed_validation(
        self, pyramid_request, lti_registration_service, views
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_
        del pyramid_request.POST["auth_login_url"]

        response = views.update_registration()

        assert (
            response["registration"] == lti_registration_service.get_by_id.return_value
        )
        assert pyramid_request.session.peek_flash("validation")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {}
        return pyramid_request

    @pytest.fixture
    def with_form_submission(self, pyramid_request):
        pyramid_request.content_type = pyramid_request.headers["content-type"] = (
            "multipart/form-data"
        )
        registration_data = {
            "issuer": "http://issuer.com",
            "client_id": "CLIENT_ID",
            "auth_login_url": "http://auth-login-url.com",
            "key_set_url": "http://key-set-url.com",
            "token_url": "http://token-url.com",
        }
        # Real pyramid request have the same params available
        # via POST and params
        pyramid_request.POST.update(registration_data)
        pyramid_request.params.update(registration_data)

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminLTIRegistrationViews(pyramid_request)
