from dataclasses import dataclass


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

    _current_region: Region = None

    @classmethod
    def get_region(cls) -> Region:
        """
        Get the region this app is running in.

        :raises ValueError: If the active region has not been set
        """
        if cls._current_region is None:
            raise ValueError(
                "You must set the active region with `set_region()` "
                "before it can be accessed"
            )

        return cls._current_region

    @classmethod
    def set_region(cls, authority: str):
        """
        Set the region this app is running in.

        This is intended to be called once and accessed as a singleton via
        `get_region()`.
        :param authority: The H authority for this app.

        :raises ValueError: If the authority provided doesn't match a region
        """
        try:
            cls._current_region = cls._AUTHORITY_MAP[authority]
        except KeyError as err:
            raise ValueError(
                f"Cannot find a region for the authority '{authority}'"
            ) from err


def includeme(config):
    config.add_request_method(
        lambda _request: Regions.get_region(),
        name="region",
        property=True,
        reify=True,
    )
