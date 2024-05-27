from hubspot import HubSpot


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

    @classmethod
    def _get_objects(cls, accessor, fields: list[str]):
        return accessor.get_all(properties=fields)
