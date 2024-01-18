from lms.models import Region


class RegionService:
    def __init__(self, region_code: str, region_name: str, authority: str):
        self._region_code = region_code
        self._region_name = region_name
        self._authority = authority

    def get(self) -> Region:
        """Return the region that the app is currently running in."""
        return Region(
            code=self._region_code,
            name=self._region_name,
            authority=self._authority,
        )


def factory(_context, request) -> RegionService:
    return RegionService(
        region_code=request.registry.settings["region_code"],
        region_name=request.registry.settings["region_name"],
        authority=request.registry.settings["h_authority"],
    )
