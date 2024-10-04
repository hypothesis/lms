from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column


class CreatedUpdatedMixin:
    created: Mapped[datetime] = mapped_column(server_default=sa.func.now())
    updated: Mapped[datetime] = mapped_column(
        server_default=sa.func.now(), onupdate=sa.func.now()
    )
