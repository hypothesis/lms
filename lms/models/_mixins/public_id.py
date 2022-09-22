from base64 import urlsafe_b64encode
from uuid import uuid4

import sqlalchemy as sa

from lms.models.region import Region


class PublicIdMixin:
    _public_id = sa.Column(
        "public_id",
        sa.UnicodeText(),
        nullable=False,
        unique=True,
        # We don't use a standard UUID-4 format here as they are common in Tool
        # Consumer Instance GUIDs, and might be confused for them. These also
        # happen to be shorter and guaranteed URL safe.
        default=lambda: urlsafe_b64encode(uuid4().bytes).decode("ascii").rstrip("="),
    )
    """
    A human readable URL safe public id.

    Although this is a GUID the DB can only enforce that this is only locally
    unique to the LMS instance. For this reason the `public_id()` accessor
    should be used instead which provides a fully qualified id.
    """

    public_id_model_code = None
    """The short code which identifies this type of model."""

    def public_id(self, region: Region) -> str:
        """
        Get the globally unique id which also indicates the region.

        This returns vales with prefixes like 'us.' or 'ca.'.

        This is useful if you only have the id, but don't know which region you
        should be looking for it in and is the only id suitable for sharing
        outside a single region LMS context.
        """

        # We use '.' as the separator here because it's not in base64, but it
        # is URL safe. The other option is '~'.
        # See: https://www.ietf.org/rfc/rfc3986.txt (2.3)
        # >    unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
        return f"{region.code}.lms.{self.public_id_model_code}.{self._public_id}"
