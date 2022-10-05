from typing import Optional

import sqlalchemy as sa
from sqlalchemy.ext.hybrid import Comparator, hybrid_property

from lms.models.public_id import PublicId
from lms.models.region import Regions


class _PublicIdComparator(Comparator):  # pylint: disable=abstract-method
    """A comparator for covering over details of comparing public ids."""

    def __eq__(self, other):
        return (
            self.__clause_element__()
            == PublicId.parse(
                # Using str here allows us to accept a public id object
                public_id=str(other),
                expect_model_code=self.expression.class_.public_id_model_code,
                expect_region=Regions.get_region(),
            ).instance_id
        )


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

    @hybrid_property
    def public_id(self) -> Optional[str]:
        """Get the globally unique id which also indicates the region."""

        if not self._public_id:
            return None

        return str(
            PublicId(
                region=Regions.get_region(),
                model_code=self.public_id_model_code,
                instance_id=self._public_id,
            )
        )

    @public_id.comparator
    def public_id(self):
        return _PublicIdComparator(self._public_id)
