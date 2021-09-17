from lms.views.onedrive import redirect_uri


def test_redirect_uri(pyramid_request):
    assert redirect_uri(pyramid_request) == {}
