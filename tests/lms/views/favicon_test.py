from lms.views import favicon


def test_favicon(pyramid_request):
    response = favicon.favicon(pyramid_request)

    assert response.status_int == 200
    assert response.headers["Content-Type"] == "image/vnd.microsoft.icon"
