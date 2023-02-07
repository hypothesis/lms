from lms.views.admin import index, logged_out, notfound
from tests.matchers import temporary_redirect_to


def test_logged_out_redirects_to_login(pyramid_request):
    response = logged_out(pyramid_request)

    assert response.status_code == 302

    assert response == temporary_redirect_to(
        pyramid_request.route_url(
            "pyramid_googleauth.login", _query={"next": pyramid_request.url}
        )
    )


def test_not_found_view(pyramid_request):
    response = notfound(pyramid_request)

    assert response.status_code == 404


def test_index(pyramid_request):
    response = index(pyramid_request)

    assert response == temporary_redirect_to(
        pyramid_request.route_url("admin.instance.search")
    )
