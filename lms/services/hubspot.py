import os
from operator import itemgetter


import os.path
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Generator, Iterable, List, Optional, Set

from hubspot import HubSpot
from hubspot.crm.associations import BatchInputPublicObjectId
from hubspot.crm.contacts import Filter, FilterGroup, PublicObjectSearchRequest
from hubspot.crm.objects.exceptions import ApiException


RATE_LIMIT_SECONDS = 5


def date_or_timestamp(value):
    """
    Format either timestamp or already formatted dates as YYYY-MM-DD.

    We seem to be getting different formats for the same fields,
    coerce them to always be string formated dates.
    """
    try:
        return datetime.fromtimestamp(int(value) / 1000).strftime("%Y-%m-%d")
    except ValueError:
        # Date is already formatted, return it verbatim
        return value


@dataclass
class Field:
    """Define a mapping from a remote field to a chosen key."""

    hs_field: str
    key: str = None
    mapping: Optional[Callable] = None

    def __post_init__(self):
        if not self.key:
            self.key = self.hs_field


@dataclass
class HubspotClient:
    """A nicer client for the Hubspot API."""

    private_app_key: str
    api_client: HubSpot = None

    # From: https://developers.hubspot.com/docs/api/crm/imports
    class ObjectType:  # pylint: disable=too-few-public-methods
        """Hubspot codes for different entity types."""

        CONTACT = "0-1"
        COMPANY = "0-2"
        DEAL = "0-3"
        NOTES = "0-4"
        TICKET = "0-5"

    # From: https://developers.hubspot.com/docs/api/crm/associations/v3
    class AssociationObjectType(Enum):
        CONTACT = "Contacts"
        COMPANY = "Companies"
        DEAL = "Deals"
        TICKET = "Tickets"
        # There are more, but I don't think we'll ever use them

    class IDType:  # pylint: disable=too-few-public-methods
        """Hubspot codes for different field types."""

        PRIMARY_KEY = "HUBSPOT_OBJECT_ID"
        REGULAR_FIELD = None

    def __post_init__(self):
        self.api_client = HubSpot()
        self.api_client.access_token = self.private_app_key

    ASSOCIATIONS_BATCH_SIZE = 11000

    def get_associations(
        self,
        from_type: AssociationObjectType,
        to_type: AssociationObjectType,
        object_ids: List,
    ) -> Set:
        """Get inter object relationships.

        :param from_type: Object on the left hand side of the relationship
        :param to_type: Object on the right hand side of the relationship
        :param object_ids: Object ids of the left hand side objects
        """

        # For reasons unclear, we appear to get duplicate entries in the return
        # values, so we'll use a set to dedupe them
        relations = set()

        # 11k is the maximum we can ask for at once from Hubspot
        for id_chunk in chunk(object_ids, chunk_size=self.ASSOCIATIONS_BATCH_SIZE):
            results = self.api_client.crm.associations.batch_api.read(
                from_object_type=from_type.value,
                to_object_type=to_type.value,
                batch_input_public_object_id=BatchInputPublicObjectId(
                    # Dedupe ids in-case we are provided the same one twice
                    inputs=list(set(str(object_id) for object_id in id_chunk))
                ),
            )

            for result in results.results:
                for to_result in result.to:
                    # pylint: disable=protected-access
                    # This just appears to be part of the goofy interface
                    relations.add((result._from.id, to_result.id))

        return relations

    def get_companies(self, fields: Iterable[Field]) -> Generator:
        """Get companies from Hubspot.

        :param fields: A list of fields to get from Hubspot
        """

        yield from self._get_objects(self.api_client.crm.companies, fields)

    def get_contacts(self, fields: Iterable[Field]) -> Generator:
        """Get contacts from Hubspot.

        :param fields: A list of fields to get from Hubspot
        """

        yield from self._get_objects(self.api_client.crm.contacts, fields)

    def get_contacts_by_email(self, emails, fields: Iterable[Field]):
        # We can't have more than 100 items in an IN query, we also can't have
        # more than 3000 chars in our total request.
        for email_batch in chunk_with_max_len(emails, chunk_size=100, max_chars=2000):
            yield from self._get_contacts_by_email(
                email_batch=email_batch, fields=fields, limit=100
            )

    def _get_contacts_by_email(
        self, email_batch, fields: Iterable[Field], limit, max_retries=5
    ):
        # Pick the largest size we are allowed
        limit = max(limit, 100)

        # Example of searching here:
        # https://github.com/HubSpot/sample-apps-search-results-iterating/blob/main/python/cli.py
        # That demonstrates pagination, which we are hoping we can get away
        # without because we ask for 100 emails max.

        filter_ = Filter(property_name="email", operator="IN", values=list(email_batch))
        request = PublicObjectSearchRequest(
            limit=limit,
            properties=[field.hs_field for field in fields],
            filter_groups=[FilterGroup(filters=[filter_])],
        )

        # Example of the retry mechanism here:
        # https://github.com/HubSpot/sample-apps-rate-limit/blob/master/python/cli.py
        # Which has been updated to not end-up with unassigned response object
        retries = 0
        while True:
            try:
                response = self.api_client.crm.contacts.search_api.do_search(request)
                break
            except ApiException as err:
                if (retries < max_retries) and err.status == 429:
                    print(
                        f"Rate limit exceeded, retrying in {RATE_LIMIT_SECONDS} seconds..."
                    )
                    time.sleep(RATE_LIMIT_SECONDS)
                    retries += 1
                else:
                    raise  # Reraise the exception if it's not a rate limit error

        if len(response.results) == limit:
            print("Potential pagination error! We got the same size as our batch size")

        return [self._map_item(item, fields) for item in response.results]

    def get_deals(self, fields: Iterable[Field]) -> Generator:
        """Get deals from Hubspot.

        :param fields: A list of fields to get from Hubspot
        """

        yield from self._get_objects(self.api_client.crm.deals, fields)

    def get_owners(self):
        """Get a list of the owners."""

        return (owner.to_dict() for owner in self.api_client.crm.owners.get_all())

    def get_properties(self, object_type):
        """
        Get the properties for a given object type.

        This is useful for trying to work out what a property you want is
        called by Hubspot internally.
        """

        return (
            prop.to_dict()
            for prop in self.api_client.crm.properties.core_api.get_all(
                object_type
            ).results
        )

    @classmethod
    def parse_teams_from_owners(cls, owners):
        """Parse owner team relations and teams from owners."""

        teams_by_id = {}
        owner_team = []

        for owner in owners:
            if not owner["teams"]:
                continue

            for team in owner["teams"]:
                teams_by_id[team["id"]] = team
                owner_team.append(
                    {"owner_id": int(owner["id"]), "team_id": int(team["id"])}
                )

        # Sort and convert ids to ints
        teams = list(teams_by_id.values())
        for team in teams:
            team["id"] = int(team["id"])

        return owner_team, teams

    @classmethod
    def _get_objects(cls, accessor, fields: Iterable[Field]):
        for item in accessor.get_all(properties=[field.hs_field for field in fields]):
            yield cls._map_item(item, fields)

    @classmethod
    def _map_item(cls, item, fields: Iterable[Field]):
        result = {}
        for field in fields:
            value = item.properties.get(field.hs_field) or None
            if value and field.mapping:
                value = field.mapping(value)

            result[field.key] = value

        return result


# The API docs link you here, but it doesn't show the API keys for properties
# https://knowledge.hubspot.com/companies/hubspot-crm-default-company-properties
# Use `api_client.get_properties(api_client.ObjectType.COMPANY)` to get details
COMPANY_FIELDS = (
    Field("hs_object_id", "id", mapping=int),
    Field("name", mapping=str),
    Field("lms_organization_id", mapping=str),
    Field("lifecyclestage", "life_cycle_stage", mapping=str),
    # Owners
    Field("hubspot_owner_id", "company_owner_id", mapping=int),
    Field("owner__success", "success_owner_id", mapping=int),
    # Cohort
    Field(
        "cohort__pilot_first_date", "cohort_pilot_first_date", mapping=date_or_timestamp
    ),
    Field(
        "cohort__subscription_first_date",
        "cohort_subscription_first_date",
        mapping=date_or_timestamp,
    ),
    # Deals
    Field("current_deal__services_start", "current_deal_services_start"),
    Field("current_deal__services_end", "current_deal_services_end"),
    Field("current_deal__amount", "current_deal_amount", mapping=float),
    Field(
        "current_deal__users_contracted", "current_deal_users_contracted", mapping=int
    ),
)

# The API docs link you here, but it doesn't show the API keys for properties
# https://knowledge.hubspot.com/crm-deals/hubspots-default-deal-properties
# Use `api_client.get_properties(api_client.ObjectType.DEAL)` to get details
DEAL_FIELDS = (
    Field("hs_object_id", "id", mapping=int),
    Field("dealname", "name", mapping=str),
    Field("services_start"),
    Field("services_end"),
    # We really should have currency, but I can't work out the name for it
    Field("amount", mapping=float),
)

COMPANY_DEAL_FIELDS = (
    Field("company_id", mapping=int),
    Field("deal_id", mapping=int),
)


def filter_owner(owner):
    """Convert the values that come from Hubspot into the shape we want."""

    first_name = owner["first_name"]
    last_name = owner["last_name"]
    email = owner["email"]

    # Try and cobble together a representative name
    if first_name and last_name:
        name = f"{first_name} {last_name}"
    elif first_name or last_name:
        name = first_name or last_name
    elif email:
        name = email.split("@")[0].title()
    else:
        name = None

    return {
        "id": owner["id"],
        "first_name": first_name or None,
        "last_name": last_name or None,
        "name": name,
        "email": email or None,
        "archived": bool(owner["archived"]),
    }


OWNERS_FIELDS = (
    Field("id"),
    Field("first_name", mapping=str),
    Field("last_name", mapping=str),
    Field("name", mapping=str),
    Field("email", mapping=str),
    Field("archived", mapping=bool),
)


def filter_team(team):
    """Convert the values that come from Hubspot into the shape we want."""

    return {"id": int(team["id"]), "name": team["name"]}


TEAMS_FIELDS = (Field("id"), Field("name"))

OWNER_TEAMS_FIELDS = (Field("owner_id"), Field("team_id"))


def __main__():
    api_client = HubspotClient(private_app_key=os.environ["HUBSPOT_API_KEY"])

    # Do everything about getting data before we start, so we don't kill the
    # DB, then have a long pause before we put things back in. This might eat
    # some memory. So we could stream to disk if required or something.
    print("Getting Hubspot data...")

    print("\tGetting owners and teams...")

    owners = list(api_client.get_owners())
    owner_teams, teams = api_client.parse_teams_from_owners(owners)
    owners = [filter_owner(owner) for owner in owners]
    owners = list(sorted(owners, key=itemgetter("id")))
    teams = [filter_team(teams) for teams in teams]
    teams = list(sorted(teams, key=itemgetter("id")))

    print("\tCompanies...")
    companies = list(api_client.get_companies(COMPANY_FIELDS))
    import pdb

    pdb.set_trace()

    print("\tDeals...")
    deals = list(api_client.get_deals(DEAL_FIELDS))
    _sort_deal_dates(deals)

    print("\tCompany deal associations...")
    company_deals = [
        {"company_id": company_id, "deal_id": deal_id}
        for company_id, deal_id in api_client.get_associations(
            from_type=api_client.AssociationObjectType.COMPANY,
            to_type=api_client.AssociationObjectType.DEAL,
            object_ids=[company["id"] for company in companies],
        )
    ]

    print("Inserting Hubspot company data...")

    print("\tOwners...")
    import_to_table(
        connection=connection,
        table_name="hubspot.owners",
        items=owners,
        fields=OWNERS_FIELDS,
    )

    print("\tTeams...")
    import_to_table(
        connection=connection,
        table_name="hubspot.teams",
        items=teams,
        fields=TEAMS_FIELDS,
    )

    print("\tOwner teams...")
    import_to_table(
        connection=connection,
        table_name="hubspot.owner_teams",
        items=owner_teams,
        fields=OWNER_TEAMS_FIELDS,
    )

    print("\tCompanies...")
    import_to_table(
        connection=connection,
        table_name="hubspot.companies_raw",
        items=companies,
        fields=COMPANY_FIELDS,
    )

    print("\tDeals...")
    import_to_table(
        connection=connection,
        table_name="hubspot.deals",
        items=deals,
        fields=DEAL_FIELDS,
    )

    print("\tCompany deal associations...")
    import_to_table(
        connection=connection,
        table_name="hubspot.company_deals",
        items=company_deals,
        fields=COMPANY_DEAL_FIELDS,
    )


def _sort_deal_dates(deals):
    """Ensure the start of a deal comes before the end.

    This should be true, but as these values are entered by people there's
    nothing really stopping them from being put in backwards, which will cause
    Postgres conniptions
    """
    for deal in deals:
        services_start, services_end = deal["services_start"], deal["services_end"]
        if services_start and services_end:
            deal["services_start"] = min(services_start, services_end)
            deal["services_end"] = max(services_start, services_end)
