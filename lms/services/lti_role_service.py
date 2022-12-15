from typing import List

from sqlalchemy.orm import Session

from lms.models import LTIRole


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


def service_factory(_context, request) -> LTIRoleService:
    """Create an LTIRoleService object."""

    return LTIRoleService(db_session=request.db)
