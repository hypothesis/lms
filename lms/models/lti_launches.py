from datetime import datetime

import sqlalchemy as sa

from lms.db import BASE


class LtiLaunches(BASE):
    """Track each LTI launch."""

    __tablename__ = "lti_launches"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    created = sa.Column(sa.TIMESTAMP, default=datetime.utcnow)
    context_id = sa.Column(sa.Unicode)
    lti_key = sa.Column(sa.Unicode)

    @classmethod
    def add(cls, db, context_id, oauth_consumer_key):
        """Add a record of an LTI launch to the database."""
        db.add(LtiLaunches(context_id=context_id, lti_key=oauth_consumer_key))
