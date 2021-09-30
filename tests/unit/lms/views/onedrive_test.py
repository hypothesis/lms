from unittest.mock import sentinel

from lms.views.onedrive import redirect_uri, verify_domain


def test_redirect_uri(pyramid_request):
    assert redirect_uri(pyramid_request) == {}


def test_verify_domain(pyramid_request):
    pyramid_request.registry.settings["onedrive_client_id"] = sentinel.client_id

    assert verify_domain(pyramid_request) == {
        "associatedApplications": [{"applicationId": sentinel.client_id}]
    }
