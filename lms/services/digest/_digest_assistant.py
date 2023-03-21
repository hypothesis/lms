from typing import Iterable, List

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import aggregate_order_by

from lms.models import AssignmentGrouping, AssignmentMembership, Grouping, LTIRole, User
from lms.models.lti_role import RoleScope, RoleType
from lms.services.digest._models import HCourse, HUser


class DigestAssistant:
    """A close collaborator of the digest service for dealing with the DB."""

    def __init__(self, db_session):
        self._db = db_session

    def get_h_users(self, h_userids: Iterable[str]) -> List[HUser]:
        """
        Get H users with a username and email.

        This will pick the most recently non-null emails and display names for
        the user.

        :param h_userids: List of H userids (e.g. 'acct:user@lms.example.com')
        """

        query = (
            # The column names here must match the HUser attributes
            sa.select(
                User.h_userid,
                # Aggregate all the emails in order of most recently updated
                # then filter out any which are NULL and pick the first.
                sa.func.array_agg(aggregate_order_by(User.email, User.updated.desc()))
                .filter(User.email.isnot(None))[1]
                .label("email"),
                # Similar for the display name
                sa.func.array_agg(
                    aggregate_order_by(User.display_name, User.updated.desc())
                )
                .filter(User.display_name.isnot(None))[1]
                .label("name"),
            )
            .where(User.h_userid.in_(h_userids))
            .group_by(User.h_userid)
        )

        return self._query_to_dataclass(query, HUser)

    def get_h_courses(self, authority_provided_ids: Iterable[str]) -> List[HCourse]:
        """
        Get courses along with any child sections and teachers.

        This will look for any courses which have the given authority provided
        id, or have children with the given authority provided id.

        This will return a list of course object which includes other authority
        provided ids which might link to this group (from sections etc.) and
        a list of H userids for instructors in the course.

        :param authority_provided_ids: A list of authority provided ids to
            start the search.
        """

        courses_model = sa.orm.aliased(Grouping, name="courses")

        query = (
            # The names here must match the HCourse attributes
            sa.select(
                courses_model.authority_provided_id,
                courses_model.lms_name.label("title"),
                sa.func.array_agg(sa.distinct(Grouping.authority_provided_id)).label(
                    "aka"
                ),
                sa.func.array_agg(sa.distinct(User.h_userid)).label("instructors"),
            )
            # Find the groups which have the courses as parents, also include
            # the course itself for convenience
            .join(
                Grouping,
                sa.or_(
                    Grouping.id == courses_model.id,
                    Grouping.parent_id == courses_model.id,
                ),
            )
            # Join on all the tables required to list the teachers for these courses
            .join(AssignmentGrouping, AssignmentGrouping.grouping_id == Grouping.id)
            .join(
                AssignmentMembership,
                AssignmentMembership.assignment_id == AssignmentGrouping.assignment_id,
            )
            .join(
                LTIRole,
                sa.and_(
                    AssignmentMembership.lti_role_id == LTIRole.id,
                    LTIRole.type == RoleType.INSTRUCTOR,
                    LTIRole.scope == RoleScope.COURSE,
                ),
            )
            .join(User, User.id == AssignmentMembership.user_id)
            # Filter to the courses we are interested in using a sub-query to
            # find the courses connected to the given authority provided ids
            .where(
                courses_model.id.in_(
                    sa.select(
                        sa.case(
                            # If the parent is null, we are the root
                            [(Grouping.parent_id.is_(None), Grouping.id)],
                            # Otherwise we want the parent id not this one
                            else_=Grouping.parent_id,
                        )
                    ).where(Grouping.authority_provided_id.in_(authority_provided_ids))
                )
            )
            .group_by(courses_model.authority_provided_id, courses_model.lms_name)
        )

        return self._query_to_dataclass(query, HCourse)

    def _query_to_dataclass(self, query, model_class):
        """Convert the results of a query into a list of dataclass objects."""

        # As per https://stackoverflow.com/questions/1958219/how-to-convert-sqlalchemy-row-object-to-a-python-dict
        # The access to a private method is suggested by one of the authors of
        # SQLAlchemy.
        # pylint: disable=protected-access
        return [model_class(**row._mapping) for row in self._db.execute(query)]
