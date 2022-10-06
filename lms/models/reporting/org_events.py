import sqlalchemy as sa
import logging
from sqlalchemy import select, func, column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import PrimaryKeyConstraint


from lms.db import BASE
from lms.models import Organization, Event, ApplicationInstance

LOG = logging.getLogger(__name__)


class RollUpOrganizationEvents(BASE):
    __tablename__ = "rollup_organization_events"

    organization_id = sa.Column(
        sa.Integer(), sa.ForeignKey("organization.id"), nullable=True
    )
    organization = sa.orm.relationship("Organization")

    event_type_id = sa.Column(
        sa.Integer(), sa.ForeignKey("event_type.id", ondelete="cascade"), index=True
    )
    event_type = sa.orm.relationship("EventType")

    timestamp = sa.Column(sa.DateTime(), nullable=False, index=True)

    count = sa.Column(sa.Integer(), nullable=False)

    __table_args__ = (PrimaryKeyConstraint(organization_id, event_type_id, timestamp),)

    @classmethod
    def rollup(cls, db_session, regenerate=False):
        # Query the generates the full table of counts
        query = (
            select(
                Organization.id.label("organization_id"),
                Event.type_id.label("event_type_id"),
                func.date_trunc("day", Event.timestamp).label("day"),
                func.count(Event.id).label("count"),
            )
            .select_from(Event)
            .join(ApplicationInstance)
            .join(Organization)
            .group_by(
                Organization.id,
                Event.type_id,
                func.date_trunc("day", Event.timestamp),
            )
        )
        if not regenerate:
            # Filter by the current day when updating periodically
            query = query.where(Event.timestamp >= func.date_trunc("day", func.now()))

        insert_stmt = insert(cls).from_select(
            ["organization_id", "event_type_id", "timestamp", "count"], query
        )

        result = db_session.execute(
            # When finding a corresponding row already present in the table, update the count
            insert_stmt.on_conflict_do_update(
                index_elements=[
                    cls.organization_id,
                    cls.event_type_id,
                    cls.timestamp,
                ],
                set_={"count": insert_stmt.excluded.count},
            )
        )
        LOG.info(f"{cls.__name__} rollup affected {result.rowcount} rows")
