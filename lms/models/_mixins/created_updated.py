from dataclasses import dataclass
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column


class CreatedUpdatedMixin:
    created: Mapped[datetime] = mapped_column(server_default=sa.func.now())
    updated: Mapped[datetime] = mapped_column(
        server_default=sa.func.now(), onupdate=sa.func.now()
    )


@dataclass
class CreatedUpdatedMixinAsDataClass:
    """Duplicate of CreatedUpdatedMixin but compatible with models that use MappedAsDataclass."""

    created: Mapped[datetime] = mapped_column(server_default=sa.func.now(), repr=False)
    updated: Mapped[datetime] = mapped_column(
        server_default=sa.func.now(), onupdate=sa.func.now(), repr=False
    )
