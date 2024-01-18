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
