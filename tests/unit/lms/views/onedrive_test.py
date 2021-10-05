import json
from unittest.mock import sentinel

from lms.views.onedrive import redirect_uri, verify_domain


def test_redirect_uri(pyramid_request):
    assert redirect_uri(pyramid_request) == {}


def test_verify_domain(pyramid_request):
    pyramid_request.registry.settings["onedrive_client_id"] = sentinel.client_id

    assert json.loads(verify_domain(pyramid_request).text) == {
        "associatedApplications": [{"applicationId": f"{sentinel.client_id}"}]
    }


def test_verify_domain_includes_length(pyramid_request):
    pyramid_request.registry.settings["onedrive_client_id"] = sentinel.client_id

    response = verify_domain(pyramid_request)

    assert response.content_length == len(response.text)
