from dataclasses import dataclass

from pyramid.request import Request


@dataclass(frozen=True)
class Region:
    """Codes and details related to a deployment region."""

    code: str
    """Region code (e.g. ISO 3166 alpha-2 country code)."""

    name: str
    """Human readable description of the region."""

    authority: str
    """Associated Hypothesis authority."""


class Regions:
    """A collection of all the regions as an enum like object."""

    # As region objects are frozen, these can be directly compared like enums
    US = Region(code="us", name="Worldwide (U.S.)", authority="lms.hypothes.is")
    CA = Region(code="ca", name="Canada", authority="lms.ca.hypothes.is")
    ALL = US, CA

    _AUTHORITY_MAP = {region.authority: region for region in ALL}
    _CODE_MAP = {region.code: region for region in ALL}

    @classmethod
    def from_code(cls, code: str) -> Region:
        """
        Get a region object based on its code.

        :raises ValueError: If no valid region can be found.
        """
        try:
            return cls._CODE_MAP[code]
        except KeyError as err:
            raise ValueError(f"Cannot find a region for the code '{code}'") from err

    @classmethod
    def from_request(cls, request: Request) -> Region:
        """
        Get a region object based on a request.

        :raises ValueError: If no valid region can be found.
        """
        authority = request.registry.settings["h_authority"]

        try:
            return cls._AUTHORITY_MAP[authority]
        except KeyError as err:
            raise ValueError(
                f"Cannot find a region for the authority '{authority}'"
            ) from err


def includeme(config):
    config.add_request_method(
        Regions.from_request, name="region", property=True, reify=True
    )
