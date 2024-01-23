import functools
from unittest import mock

import pytest

TEST_SETTINGS = {
    "dev": False,
    "via_url": "http://TEST_VIA_SERVER.is/",
    "jwt_secret": "test_secret",
    "google_client_id": "fake_client_id",
    "google_developer_key": "fake_developer_key",
    "lms_secret": "TEST_LMS_SECRET",
    "aes_secret": b"TSeQ7E3dzbHgu5ydX2xCrKJiXTmfJbOe",
    "jinja2.filters": {
        "static_path": "pyramid_jinja2.filters:static_path_filter",
        "static_url": "pyramid_jinja2.filters:static_url_filter",
    },
    "h_client_id": "TEST_CLIENT_ID",
    "h_client_secret": "TEST_CLIENT_SECRET",
    "h_jwt_client_id": "TEST_JWT_CLIENT_ID",
    "h_jwt_client_secret": "TEST_JWT_CLIENT_SECRET",
    "h_authority": "lms.hypothes.is",
    "region_code": "us",
    "h_api_url_public": "https://h.example.com/api/",
    "h_api_url_private": "https://h.example.com/private/api/",
    "rpc_allowed_origins": ["http://localhost:5000"],
    "oauth2_state_secret": "test_oauth2_state_secret",
    "session_cookie_secret": "notasecret",
    "via_secret": "not_a_secret",
    "blackboard_api_client_id": "test_blackboard_api_client_id",
    "blackboard_api_client_secret": "test_blackboard_api_client_secret",
    "vitalsource_api_key": "test_vs_api_key",
    "disable_key_rotation": False,
    "admin_users": [],
    "email_preferences_secret": "test_email_preferences_secret",
}


def autopatcher(request, target, **kwargs):
    """Patch and cleanup automatically. Wraps :py:func:`mock.patch`."""
    options = {"autospec": True}
    options.update(kwargs)
    patcher = mock.patch(target, **options)
    obj = patcher.start()
    request.addfinalizer(patcher.stop)
    return obj


@pytest.fixture
def patch(request):
    return functools.partial(autopatcher, request)
