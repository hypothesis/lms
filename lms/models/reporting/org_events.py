import sqlalchemy as sa
import logging
from sqlalchemy import select, func, column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import PrimaryKeyConstraint


from lms.db import BASE
from lms.models import Organization, Event, ApplicationInstance

LOG = logging.getLogger(__name__)


class RollUpMixin:
    rollup_index_elements = []
    """Which columns are unique in the rollup table to find conflicts"""
    rollup_query = None
    """Query that produces the full row set of the rollup table"""
    rollup_condition = None
    """Condition to add to `rollup_query` when running this periodically"""

    @classmethod
    def rollup(cls, db_session, regenerate=False):
        query = cls.rollup_query()
        if not regenerate:
            # Filter by the current day when updating periodically
            query = query.where(cls.rollup_condition)

        # We are assuming here that query will
        # return a value (even if it's a null) for each column of the rollup table
        insert_stmt = insert(cls).from_select(cls.columns(), query)

        result = db_session.execute(
            # When finding a corresponding row already present in the table, update the count
            insert_stmt.on_conflict_do_update(
                index_elements=cls.rollup_index_elements,
                set_={"count": insert_stmt.excluded.count},
            )
        )
        LOG.info(f"{cls.__name__} rollup affected {result.rowcount} rows")


class RollUpOrganizationEvents(BASE, RollUpMixin):
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

    rollup_index_elements = [organization_id, event_type_id, timestamp]
    rollup_condition = Event.timestamp >= func.date_trunc("day", func.now())

    @classmethod
    def rollup_query(cls):
        return (
            select(
                Organization.id.label("organization_id"),
                Event.type_id.label("event_type_id"),
                func.date_trunc("day", Event.timestamp).label("day"),
                func.count(Event.id).label("count"),
            )
            .select_from(Event)
            .join(ApplicationInstance)
            .join(Organization)
            .group_by(Organization.id, Event.type_id, column("day"))
        )
