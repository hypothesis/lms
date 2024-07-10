import json
from datetime import date
from unittest.mock import create_autospec, sentinel

import pytest
from hubspot import HubSpot

from lms.services.hubspot._client import HubSpotClient


class TestHubSpotClient:
    def test_get_companies(self, api_client, svc):
        companies = list(svc.get_companies())

        api_client.crm.companies.get_all.assert_called_once_with(
            properties=[
                "hs_object_id",
                "name",
                "lms_organization_id",
                "current_deal__services_start",
                "current_deal__services_end",
            ]
        )
        assert companies == list(api_client.crm.companies.get_all.return_value)

    def test_import_billables(self, api_client, svc, csv, NamedTemporaryFile):
        svc.import_billables(
            [(sentinel.id, sentinel.teachers, sentinel.users)], date(2024, 1, 1)
        )

        NamedTemporaryFile.assert_called_once_with(mode="w", suffix=".csv")
        csv.writer.assert_called_once()
        csv.writer.return_value.writerow.assert_called_once_with(
            (sentinel.id, sentinel.teachers, sentinel.users)
        )
        api_client.crm.imports.core_api.create.assert_called_once_with(
            import_request=json.dumps(
                {
                    "name": "contract_year_import_2024-01-01",
                    "files": [
                        {
                            "fileName": "IMPORT.csv",
                            "fileFormat": "CSV",
                            "fileImportPage": {
                                "hasHeader": False,
                                "columnMappings": [
                                    {
                                        "columnObjectTypeId": "0-2",
                                        "columnName": "hs_object_id",
                                        "propertyName": "hs_object_id",
                                        "idColumnType": "HUBSPOT_OBJECT_ID",
                                    },
                                    {
                                        "columnObjectTypeId": "0-2",
                                        "columnName": "billable_teachers_this_contract_year",
                                        "propertyName": "billable_teachers_this_contract_year",
                                        "idColumnType": None,
                                    },
                                    {
                                        "columnObjectTypeId": "0-2",
                                        "columnName": "billable_users_this_contract_year",
                                        "propertyName": "billable_users_this_contract_year",
                                        "idColumnType": None,
                                    },
                                ],
                            },
                        }
                    ],
                    "dateFormat": "YEAR_MONTH_DAY",
                }
            ),
            files=["IMPORT.csv"],
            async_req=False,
        )

    @pytest.fixture
    def api_client(self):
        return create_autospec(HubSpot, spec_set=True, instance=True)

    @pytest.fixture
    def csv(self, patch):
        return patch("lms.services.hubspot._client.csv")

    @pytest.fixture
    def NamedTemporaryFile(self, patch):
        mock = patch("lms.services.hubspot._client.NamedTemporaryFile")
        mock.return_value.__enter__.return_value.name = "IMPORT.csv"

        return mock

    @pytest.fixture
    def svc(self, api_client):
        return HubSpotClient(api_client=api_client)
