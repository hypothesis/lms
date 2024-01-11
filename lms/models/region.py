from dataclasses import dataclass


@dataclass
class Region:
    """Codes and details related to a deployment region."""

    code: str
    """Region code (e.g. ISO 3166 alpha-2 country code)."""

    authority: str
    """Associated Hypothesis authority."""

    def __post_init__(self):
        names = {"us": "Worldwide (U.S.)", "ca": "Canada"}

        #: Human readable description of the region.
        self.name: str = names[self.code]


class Regions:
    """A collection of all the regions as an enum like object."""

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
        cls._current_region = Region(code=code, authority=authority)
