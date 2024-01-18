from base64 import urlsafe_b64encode
from dataclasses import dataclass
from uuid import uuid4

from lms.models.region import Region


class InvalidPublicId(Exception):
    """Indicate an error with the specified public id."""


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

    @classmethod
    def parse(
        cls,
        public_id: str,
        expect_model_code: str,
        expect_region: Region,
    ):
        """
        Parse a public id string into a PublicID object.

        :param public_id: Public id to parse
        :param expect_model_code: Expect the specified model code
        :param expect_region: Expect the specified region

        :raises InvalidPublicId: If the public id is malformed or any
            expectations are not met
        """
        parts = public_id.split(".")
        if not len(parts) == 4:
            raise InvalidPublicId(
                f"Malformed public id: '{public_id}'. Expected 4 dot separated parts."
            )

        region_code, app_code, model_code, instance_id = parts

        if model_code != expect_model_code:
            raise InvalidPublicId(
                f"Expected model '{expect_model_code}', found '{model_code}'"
            )

        region = Region(code=region_code, authority=expect_region.authority)

        if region != expect_region:
            raise InvalidPublicId(
                f"Expected region '{expect_region}', found '{region}'"
            )

        return cls(
            region=region,
            app_code=app_code,
            model_code=model_code,
            instance_id=instance_id,
        )

    def __str__(self):
        # Ensure we stringify to the public code naturally

        # We use '.' as the separator here because it's not in base64, but it
        # is URL safe. The other option is '~'.
        # See: https://www.ietf.org/rfc/rfc3986.txt (2.3)
        # >    unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
        return (
            f"{self.region.code}.{self.app_code}.{self.model_code}.{self.instance_id}"
        )
