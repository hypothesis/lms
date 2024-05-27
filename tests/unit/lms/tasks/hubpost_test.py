from contextlib import contextmanager

import pytest

from lms.tasks.hubspot import refresh_hubspot_data


def test_refresh_hubspot_data(hubspot_service):
    refresh_hubspot_data()

    hubspot_service.refresh_companies.assert_called_once()


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.hubspot.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
