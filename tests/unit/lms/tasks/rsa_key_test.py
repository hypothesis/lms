from contextlib import contextmanager
from unittest.mock import sentinel

import pytest
from freezegun import freeze_time

from lms.tasks.rsa_key import TARGET_KEYS, rotate_keys


@freeze_time("2022-06-21 12:00:00")
def test_rotate_keys(pyramid_request, rsa_key_service):
    expiration_seconds = 60 * 60
    pyramid_request.registry.settings["rsa_key_count"] = sentinel.rsa_key_count
    pyramid_request.registry.settings["rsa_key_expiration_seconds"] = expiration_seconds

    rotate_keys()

    rsa_key_service.rotate.assert_called_once_with(TARGET_KEYS)


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.rsa_key.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
