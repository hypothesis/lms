from typing import Optional

import sqlalchemy as sa

from lms.models.public_id import PublicId
from lms.models.region import Region


class PublicIdMixin:
    _public_id = sa.Column(
        "public_id",
        sa.UnicodeText(),
        nullable=False,
        unique=True,
        default=PublicId.generate_instance_id,
    )
    """
    A human readable URL safe public id.

    Although this is a GUID the DB can only enforce that this is only locally
    unique to the LMS instance. For this reason the `public_id()` accessor
    should be used instead which provides a fully qualified id.
    """

    public_id_model_code = None
    """The short code which identifies this type of model."""

    def public_id(self, region: Region) -> Optional[str]:
        """Get the globally unique id which also indicates the region."""

        if not self._public_id:
            return None

        return str(
            PublicId(
                region=region,
                model_code=self.public_id_model_code,
                instance_id=self._public_id,
            )
        )
