from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound

from lms.models.hubspot import HubSpotCompany, HubSpotDeal
from lms.services.hubspot._client import HubSpotClient
from lms.services.upsert import bulk_upsert


class HubSpotService:
    def __init__(self, db, client: HubSpotClient, region_code: str):
        self._db = db
        self._client = client
        self._region_code = region_code

    def get_commpany(self, organization_id: str) -> HubSpotCompany | None:
        print(organization_id)
        try:
            return self._db.scalars(
                select(HubSpotCompany).where(
                    HubSpotCompany.lms_organization_id == organization_id
                )
            ).one_or_none()
        except MultipleResultsFound:
            # More than one company pointing to the same org is a data entry error, ignore them.
            print("MORE THAN ONE")
            return None

    def refresh_companies(self) -> None:
        companies = self._client.get_companies()

        bulk_upsert(
            self._db,
            HubSpotCompany,
            [
                {
                    "hs_object_id": int(company.properties["hs_object_id"]),
                    "name": company.properties["name"],
                    "lms_organization_id": company.properties["lms_organization_id"],
                    "current_deal_services_start": date_or_timestamp(
                        company.properties["current_deal__services_start"]
                    ),
                    "current_deal_services_end": date_or_timestamp(
                        company.properties["current_deal__services_end"]
                    ),
                }
                for company in companies
                # Only get companies with an org ID
                if company.properties["lms_organization_id"]
                # only for the current region
                and company.properties["lms_organization_id"].startswith(
                    self._region_code
                )
            ],
            index_elements=["hs_object_id"],
            update_columns=[
                "name",
                "lms_organization_id",
                "current_deal_services_start",
                "current_deal_services_end",
            ],
        )

    def refresh_deals(self) -> None:
        deals = self._client.get_deals()

        bulk_upsert(
            self._db,
            HubSpotDeal,
            [
                {
                    "hs_object_id": int(deal.properties["hs_object_id"]),
                    "name": deal.properties["dealname"],
                    "services_start": date_or_timestamp(
                        deal.properties["services_start"]
                    ),
                    "services_end": date_or_timestamp(deal.properties["services_end"]),
                }
                for deal in deals
            ],
            index_elements=["hs_object_id"],
            update_columns=[
                "name",
                "services_start",
                "services_end",
            ],
        )

    @classmethod
    def factory(cls, context, request):
        return cls(
            db=request.db,
            client=HubSpotClient.factory(context, request),
            region_code=request.registry.settings["region_code"],
        )


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
