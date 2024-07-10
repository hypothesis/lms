from contextlib import contextmanager
from datetime import date

import pytest
from freezegun import freeze_time

from lms.tasks.hubspot import export_companies_contract_billables, refresh_hubspot_data


def test_refresh_hubspot_data(hubspot_service):
    refresh_hubspot_data()

    hubspot_service.refresh_companies.assert_called_once()


@freeze_time("2022-06-21 12:00:00")
def test_export_companies_contract_billables(hubspot_service):
    export_companies_contract_billables()

    hubspot_service.export_companies_contract_billables.assert_called_once_with(
        date(2022, 6, 21)
    )


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.hubspot.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
