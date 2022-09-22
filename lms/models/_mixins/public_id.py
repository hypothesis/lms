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

    @classmethod
    def public_id_eq(cls, public_id, region: Region):
        """
        Get a comparator for queries which asserts we match the public id.

        This is intended to be used in filter assertions as follows:

            query.filter(Model.public_id_eq(public_id, region))

        :raises InvalidPublicId: If the public id is malformed or any expectations
            are not met
        """

        return (
            cls._public_id
            == PublicId.parse(
                # Using str here allows us to accept a public id object
                public_id=str(public_id),
                expect_model_code=cls.public_id_model_code,
                expect_region=region,
            ).instance_id
        )
