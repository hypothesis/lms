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
