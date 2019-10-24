import datetime

import sqlalchemy as sa

from lms.db import BASE

__all__ = ["LISResultSourcedId"]


class LISResultSourcedId(BASE):
    """
    A record of a student's launch of a Hypothesis-configured LMS assignment.

    For some institutions (at present, BlackBoardLearn), we need to persist
    some information about students and launches to be able to provide grading
    support for instructors/graders later on.

    Data persisted here allows us to make use of APIs that support the LTI Basic
    Outcomes spec and configure the Hypothesis client appropriately for grading.

    The combination of ``oauth_consumer_key``, ``user_id``, ``context_id``,
    and ``resource_link_id`` uniquely identifies a user-assignment
    (``user_id``, ``resource_link_id``) launch within a particular course
    (``context_id``) and application install (``oauth_consumer_key``). The
    uniqueness constraint here indicates that we should only ever have one
    record per user-assignment-course-install combination.

    ``lis_result_sourcedid`` and ``lis_outcome_service_url`` allow us to
    construct the right requests to outcome (i.e. grading) APIs when needed. As
    these values can change over time (while user-assignment-course-install
    remains static), records should be updated upon subsequent launches to make
    sure these stay in sync—i.e. record should be created on first relevant
    launch and updated on each subsequent relevant launch.

    ``h_username`` and ``h_display_name`` allow us to configure the Hypothesis
    client and this application's own interface when in grading mode, as we
    won't have access to request parameters to derive this information when it
    is, at last, needed.
    """

    __tablename__ = "lis_result_sourcedid"
    __table_args__ = (
        sa.UniqueConstraint(
            "oauth_consumer_key", "user_id", "context_id", "resource_link_id"
        ),
    )

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)
    created = sa.Column(
        sa.DateTime(),
        default=datetime.datetime.utcnow,
        server_default=sa.func.now(),
        nullable=False,
    )
    updated = sa.Column(
        sa.DateTime(),
        server_default=sa.func.now(),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    lis_result_sourcedid = sa.Column(sa.UnicodeText(), nullable=False)
    lis_outcome_service_url = sa.Column(sa.UnicodeText(), nullable=False)
    oauth_consumer_key = sa.Column(sa.UnicodeText(), nullable=False)
    user_id = sa.Column(sa.UnicodeText(), nullable=False)
    context_id = sa.Column(sa.UnicodeText(), nullable=False)
    resource_link_id = sa.Column(sa.UnicodeText(), nullable=False)
    # The "family" of LMS tool, e.g. "BlackboardLearn" or "canvas"
    tool_consumer_info_product_family_code = sa.Column(sa.UnicodeText(), nullable=True)
    h_username = sa.Column(sa.UnicodeText(), nullable=False)
    h_display_name = sa.Column(sa.UnicodeText(), nullable=False)
