# -*- coding: utf-8 -*-

import sqlalchemy as sa

from lms.db import BASE


class CourseGroup(BASE):
    """
    A record of a course group that was successfully created in h.

    Maps a globally unique LTI course identifier
    (tool_consumer_instance_guid, content_id) to a Hypothesis group ID so that
    we can recall the Hypothesis pubid of the group that was created for a
    given LTI course.

    """

    __tablename__ = "course_groups"
    __table_args__ = (
        # Add a composite index of the (tool_consumer_instance_guid, context_id)
        # columns. This should make looking up course_groups table rows by
        # (tool_consumer_instance_guid, context_id), which we're expecting to do
        # often, faster.
        #
        # See:
        #
        # * http://docs.sqlalchemy.org/en/latest/core/constraints.html#indexes
        # * https://www.postgresql.org/docs/10/static/indexes.html
        sa.Index(
            "ix__course_groups_tool_consumer_instance_guid_context_id",
            "tool_consumer_instance_guid",
            "context_id",
            # Add a uniqueness constraint to the index so that two groups can't
            # have the same tool_consumer_instance_guid and context_id.
            unique=True,
        ),
    )

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    tool_consumer_instance_guid = sa.Column(sa.UnicodeText, nullable=False)
    context_id = sa.Column(sa.UnicodeText, nullable=False)
    pubid = sa.Column(sa.Text, nullable=False, unique=True)

    @classmethod
    def get(cls, db, tool_consumer_instance_guid, context_id):
        """
        Return the CourseGroup with the given properties, or None.

        Return the CourseGroup with the given tool_consumer_instance_guid and
        context_id, or None.

        """
        return (
            db.query(cls)
            .filter_by(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                context_id=context_id,
            )
            .one_or_none()
        )
