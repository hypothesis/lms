from os import environ

import sqlalchemy as sa
from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from lms.models.public_id import PublicId
from lms.models.region import Region


def _get_current_region():
    return Region(code=environ["REGION_CODE"], authority=environ["H_AUTHORITY"])


class _PublicIdComparator(Comparator):
    """A comparator for covering over details of comparing public ids."""

    def __eq__(self, other):
        return (
            self.__clause_element__()
            == PublicId.parse(
                # Using str here allows us to accept a public id object
                public_id=str(other),
                expect_model_code=self.expression.class_.public_id_model_code,
                expect_region=_get_current_region(),
            ).instance_id
        )


class PublicIdMixin:
    _public_id: Mapped[str] = mapped_column(
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

    public_id_model_code: str
    """The short code which identifies this type of model."""

    @hybrid_property
    def public_id(self) -> str | None:
        """Get the globally unique id which also indicates the region."""

        if not self._public_id:
            return None

        return str(
            PublicId(
                region=_get_current_region(),
                model_code=self.public_id_model_code,
                instance_id=self._public_id,
            )
        )

    @public_id.inplace.comparator
    def public_id_comparator(self):
        return _PublicIdComparator(self._public_id)
