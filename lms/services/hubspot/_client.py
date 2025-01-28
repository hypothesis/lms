import csv
import json
import os
from datetime import date
from enum import StrEnum
from logging import getLogger
from tempfile import NamedTemporaryFile

from hubspot import HubSpot

LOG = getLogger(__name__)


class HubSpotObjectTypeID(StrEnum):
    """Possible HubSpot objectTypeId values."""

    # From: https://developers.hubspot.com/docs/api/crm/imports
    COMPANY = "0-2"


class HubSpotClient:
    """A nicer client for the Hubspot API."""

    def __init__(self, api_client: HubSpot):
        self._api_client = api_client

    def get_companies(self):
        """Get companies from Hubspot."""
        fields = [
            "hs_object_id",
            "name",
            "lms_organization_id",
            "current_deal__services_start",
            "current_deal__services_end",
        ]
        yield from self._get_objects(self._api_client.crm.companies, fields)

    def import_billables(self, billables: list[tuple[str, int, int]], date_: date):
        """Import the given billables into HubSpot.

        :param billables: a list of (hubspot_company_id, num_unique_teachers, num_unique_users) tuples
        :param date_: date of the billable calculation.
        """
        with NamedTemporaryFile(mode="w", suffix=".csv") as csv_file:
            writer = csv.writer(csv_file)
            for row in billables:
                writer.writerow(row)
            # Ensure all rows are written to disk before we start to upload
            csv_file.flush()

            files = [
                {
                    "fileName": os.path.basename(csv_file.name),  # noqa: PTH119
                    "fileFormat": "CSV",
                    "fileImportPage": {
                        "hasHeader": False,
                        "columnMappings": [
                            {
                                "columnObjectTypeId": HubSpotObjectTypeID.COMPANY,
                                "columnName": "hs_object_id",
                                "propertyName": "hs_object_id",
                                "idColumnType": "HUBSPOT_OBJECT_ID",
                            },
                            {
                                "columnObjectTypeId": HubSpotObjectTypeID.COMPANY,
                                "columnName": "billable_teachers_this_contract_year",
                                "propertyName": "billable_teachers_this_contract_year",
                                "idColumnType": None,
                            },
                            {
                                "columnObjectTypeId": HubSpotObjectTypeID.COMPANY,
                                "columnName": "billable_users_this_contract_year",
                                "propertyName": "billable_users_this_contract_year",
                                "idColumnType": None,
                            },
                        ],
                    },
                }
            ]

            import_request = {
                "name": f"contract_year_import_{date_.isoformat()}",
                "files": files,
                "dateFormat": "YEAR_MONTH_DAY",
            }

            LOG.debug(
                "Creating HubSpot company import with %d rows",
                len(billables),
            )
            return self._api_client.crm.imports.core_api.create(
                import_request=json.dumps(import_request),
                files=[csv_file.name],
                async_req=False,
            )

    @classmethod
    def _get_objects(cls, accessor, fields: list[str]):
        return accessor.get_all(properties=fields)
