import sqlalchemy as sa

from lms.db import BASE


class CourseGroupsExportedFromH(BASE):
    """
    A read-only table holding a one-time export of groups from h.

    See: https://github.com/hypothesis/lms/issues/1787

    """

    __tablename__ = "course_groups_exported_from_h"

    authority_provided_id = sa.Column(sa.UnicodeText(), primary_key=True)
    created = sa.Column(sa.DateTime, nullable=False)
