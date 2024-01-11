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

    @classmethod
    def from_code(cls, authority: str, code: str) -> Region:
        """
        Get a region object based on its code.

        :raises ValueError: If no valid region can be found.
        """
        names = {"us": "Worldwide (U.S.)", "ca": "Canada"}

        try:
            name = names[code]
        except KeyError as err:
            raise ValueError(f"Cannot find a name for the code '{code}'") from err

        return Region(code=code, name=name, authority=authority)

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
    def set_region(cls, authority: str, code: str):
        """
        Set the region this app is running in.

        This is intended to be called once and accessed as a singleton via
        `get_region()`.

        :param authority: The H authority for this app.
        :param code: The region code for this app.

        :raises ValueError: If `code` isn't a known region code
        """
        cls._current_region = cls.from_code(authority, code)


def includeme(config):
    config.add_request_method(
        lambda _request: Regions.get_region(),
        name="region",
        property=True,
        reify=True,
    )
