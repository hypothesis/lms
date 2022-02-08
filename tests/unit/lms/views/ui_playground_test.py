from lms.views import ui_playground


def test_ui_playground(pyramid_request):
    response = ui_playground.ui_playground(pyramid_request)
    assert not response


def test_not_found_view(pyramid_request):
    response = ui_playground.notfound(pyramid_request)
    assert response.status_code == 404
