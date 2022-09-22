from base64 import urlsafe_b64encode
from dataclasses import dataclass
from uuid import uuid4

from lms.models.region import Region


@dataclass
class PublicId:
    """
    Get a globally unique value with prefixes like 'us.' or 'ca.'.

    This is useful if you only have the id, but don't know which region you
    should be looking for it in and is the only id suitable for sharing
    outside a single region LMS context.
    """

    region: Region
    """Region this model is in."""

    model_code: str
    """Short identifier of the model type."""

    app_code: str = "lms"
    """Code representing the product this model is in."""

    instance_id: str = None
    """Identifier for the specific model instance."""

    def __post_init__(self):
        if self.instance_id is None:
            self.instance_id = self.generate_instance_id()

    @classmethod
    def generate_instance_id(cls) -> str:
        """Get a new instance id."""

        # We don't use a standard UUID-4 format here as they are common in Tool
        # Consumer Instance GUIDs, and might be confused for them. These also
        # happen to be shorter and guaranteed URL safe.
        return urlsafe_b64encode(uuid4().bytes).decode("ascii").rstrip("=")

    def __str__(self):
        # Ensure we stringify to the public code naturally

        # We use '.' as the separator here because it's not in base64, but it
        # is URL safe. The other option is '~'.
        # See: https://www.ietf.org/rfc/rfc3986.txt (2.3)
        # >    unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
        return (
            f"{self.region.code}.{self.app_code}.{self.model_code}.{self.instance_id}"
        )
