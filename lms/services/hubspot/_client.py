import os.path
from enum import Enum
from typing import Callable, Generator, Iterable, List, Optional, Set

from hubspot import HubSpot
from hubspot.crm.associations import BatchInputPublicObjectId
from hubspot.crm.companies import PublicObjectSearchRequest


# From: https://developers.hubspot.com/docs/api/crm/associations/v3
class AssociationObjectType(Enum):
    CONTACT = "Contacts"
    COMPANY = "Companies"
    DEAL = "Deals"
    TICKET = "Tickets"


class HubSpotClient:
    """A nicer client for the Hubspot API."""

    def __init__(self, api_client: HubSpot):
        self._api_client = api_client

    ASSOCIATIONS_BATCH_SIZE = 11000

    def get_associations(self, from_type, to_type, object_ids: list) -> set:
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

    def get_deals(self) -> Generator:
        """Get deals from Hubspot."""
        fields = [
            "hs_object_id",
            "dealname",
            "services_start",
            "services_end",
        ]
        yield from self._get_objects(self._api_client.crm.deals, fields)

    def get_company_deals(self, companies):
        return [
            {"company_id": company_id, "deal_id": deal_id}
            for company_id, deal_id in self.get_associations(
                from_type=AssociationObjectType.COMPANY,
                to_type=AssociationObjectType.DEAL,
                object_ids=[company["id"] for company in companies],
            )
        ]

    @classmethod
    def _get_objects(cls, accessor, fields: list[str]) -> list[dict]:
        return accessor.get_all(properties=fields)

    @classmethod
    def factory(cls, _context, request):
        return cls(HubSpot(access_token=request.registry.settings["hubspot_api_key"]))
