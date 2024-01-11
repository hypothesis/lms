from lms.models import Region


class RegionService:
    def __init__(self, region_code: str, authority: str):
        self._region_code = region_code
        self._authority = authority

    def get(self) -> Region:
        """Return the region that the app is currently running in."""
        return Region(code=self._region_code, authority=self._authority)


def factory(_context, request) -> RegionService:
    return RegionService(
        region_code=request.registry.settings["region_code"],
        authority=request.registry.settings["h_authority"],
    )
