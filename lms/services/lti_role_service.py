from typing import Iterable, List

from sqlalchemy.orm import Session

from lms.models import AssignmentMembership, LTIRole, User


class LTIRoleService:
    """A service for dealing with LTIRole objects."""

    def __init__(self, db_session: Session):
        self._db = db_session

    def get_roles(self, role_description: str) -> List[LTIRole]:
        """
        Get a list of role objects for the provided strings.

        :param role_description: A comma delimited set of role strings
        """
        role_strings = [role.strip() for role in role_description.split(",")]

        # pylint: disable=no-member
        # Pylint is confused about the `in_` for some reason
        roles = self._db.query(LTIRole).filter(LTIRole.value.in_(role_strings)).all()

        for role in roles:
            # Update scope and type.
            # This is useful when the logic for those fields change, updating
            # the values in the DB and also exposing the right values in the
            # rest to the application.
            role.update_from_value()

        if missing := (set(role_strings) - set(role.value for role in roles)):
            new_roles = [LTIRole(value=value) for value in missing]
            self._db.add_all(new_roles)

            roles.extend(new_roles)

        return roles

    def get_users(self, role_type, application_instances=None) -> Iterable[User]:
        """
        Return all users who have the given role type in any context.

        For example get_users(role_type="instructor") will return all users
        who're an instructor for one or more assignments.

        If an `application_instances` argument is given (a list of
        ApplicationInstance's) then only users belonging to those application
        instances will be returned.

        This may return multiple users with the same `user_id` and `h_userid`
        but belonging to different ApplicationInstance's. This happens when a
        single LMS instance has multiple ApplicationInstance's.
        """
        query = self._db.query(User)

        if application_instances:
            query = query.filter(
                User.application_instance_id.in_(
                    [instance.id for instance in application_instances]
                )
            )

        query = (
            query.join(AssignmentMembership)
            .join(LTIRole)
            .filter(LTIRole.type == role_type)
            .order_by(User.updated.desc())
        )

        return query


def service_factory(_context, request) -> LTIRoleService:
    """Create an LTIRoleService object."""

    return LTIRoleService(db_session=request.db)
