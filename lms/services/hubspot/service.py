import os.path
from datetime import datetime

from lms.models.hubspot import HubSpotCompanyRaw
from lms.services.hubspot._client import HubSpotClient
from lms.services.upsert import bulk_upsert


class HubSpotService:
    def __init__(self, db, client: HubSpotClient):
        self._db = db
        self._client = client

    def refresh_raw_companies(self) -> None:
        companies = self._client.get_companies()

        bulk_upsert(
            self._db,
            HubSpotCompanyRaw,
            [
                {
                    "name": company.properties["name"],
                    "hs_object_id": int(company.properties["hs_object_id"]),
                    "lms_organization_id": company.properties["lms_organization_id"],
                    "current_deal_services_start": date_or_timestamp(
                        company.properties["current_deal__services_start"]
                    ),
                    "current_deal_services_end": date_or_timestamp(
                        company.properties["current_deal__services_end"]
                    ),
                }
                for company in companies
            ],
            index_elements=["hs_object_id"],
            update_columns=[
                "name",
                "lms_organization_id",
                "current_deal_services_start",
                "current_deal_services_end",
            ],
        )

    @classmethod
    def factory(cls, context, request):
        return cls(db=request.db, client=HubSpot.factory(context, request))


def date_or_timestamp(value: str | int | None) -> str | None:
    """
    Format either timestamp or already formatted dates as YYYY-MM-DD.

    We seem to be getting different formats for the same fields,
    coerce them to always be string formated dates.
    """
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000).strftime("%Y-%m-%d")
    except ValueError:
        # Date is already formatted, return it verbatim
        return value
