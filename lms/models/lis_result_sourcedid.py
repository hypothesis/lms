import sqlalchemy as sa

from lms.db import BASE


__all__ = ["LISResultSourceDID"]


class LISResultSourceDID(BASE):
    __tablename__ = "lis_result_sourcedid"
    __table_args__ = (
        sa.UniqueConstraint(
            "oauth_consumer_key", "user_id", "context_id", "resource_link_id"
        ),
    )

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)
    lis_result_sourcedid = sa.Column(sa.UnicodeText(), nullable=False)
    lis_outcome_service_url = sa.Column(sa.UnicodeText(), nullable=False)
    oauth_consumer_key = sa.Column(sa.UnicodeText(), nullable=False)
    user_id = sa.Column(sa.UnicodeText(), nullable=False)
    context_id = sa.Column(sa.UnicodeText(), nullable=False)
    resource_link_id = sa.Column(sa.UnicodeText(), nullable=False)
    username = sa.Column(sa.UnicodeText(), nullable=False)
    display_name = sa.Column(sa.UnicodeText(), nullable=False)
