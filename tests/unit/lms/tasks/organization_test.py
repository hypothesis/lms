from contextlib import contextmanager
from datetime import datetime
from unittest.mock import sentinel

import pytest

from lms.tasks.organization import generate_usage_report


def test_delete_expired_rows(organization_service):
    generate_usage_report(
        sentinel.id,
        sentinel.tag,
        "2024-01-01:00:00:00",
        "2024-02-02:00:00:00",
    )

    organization_service.generate_usage_report.assert_called_once_with(
        sentinel.id,
        sentinel.tag,
        datetime(2024, 1, 1, 0, 0, 0),
        datetime(2024, 2, 2, 0, 0, 0),
    )


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.organization.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
