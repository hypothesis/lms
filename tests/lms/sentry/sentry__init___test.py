import pytest

from lms.sentry import includeme
from lms.sentry.helpers.before_send import before_send


class TestIncludeMe(object):
    def test_it_initializes_sentry_sdk(self, os, sentry_sdk, pyramid_config):
        includeme(pyramid_config)

        sentry_sdk.init.assert_called_once_with(
            integrations=[
                sentry_sdk.integrations.pyramid.PyramidIntegration.return_value
            ],
            environment="test",
            send_default_pii=True,
            before_send=before_send,
        )


@pytest.fixture
def os(patch):
    os = patch("lms.sentry.os")
    os.environ = {"SENTRY_ENVIRONMENT": "test"}
    return os


@pytest.fixture(autouse=True)
def sentry_sdk(patch):
    return patch("lms.sentry.sentry_sdk")
