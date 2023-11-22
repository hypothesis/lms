import pytest

from lms.security import Identity
from lms.views.admin import forbidden, index, notfound
from tests.matchers import temporary_redirect_to


def test_forbidden_redirects_to_login(pyramid_request_without_userid):
    response = forbidden(pyramid_request_without_userid)

    assert response.status_code == 302

    assert response == temporary_redirect_to(
        pyramid_request_without_userid.route_url(
            "pyramid_googleauth.login",
            _query={"next": pyramid_request_without_userid.url},
        )
    )


def test_forbidden_redirects_to_index_when_permission(pyramid_request):
    response = forbidden(pyramid_request)

    assert response.status_code == 302
    assert response == temporary_redirect_to(pyramid_request.route_url("admin.index"))


def test_not_found_view(pyramid_request):
    response = notfound(pyramid_request)

    assert response.status_code == 404


def test_index(pyramid_request):
    response = index(pyramid_request)

    assert response == temporary_redirect_to(
        pyramid_request.route_url("admin.instance.search")
    )


@pytest.fixture
def pyramid_request_without_userid(pyramid_config, pyramid_request, lti_user):
    pyramid_config.testing_securitypolicy(
        userid="", identity=Identity("", [], lti_user)
    )
    return pyramid_request
