from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from lms.models import ApplicationInstance
from lms.models.lti_role import LTIRole, LTIRoleOverride, Role


class LTIRoleService:
    """A service for dealing with LTIRole objects."""

    def __init__(self, db_session: Session):
        self._db = db_session

    def get_roles(self, role_description: str) -> list[LTIRole]:
        """
        Get a list of role objects for the provided strings.

        :param role_description: A comma delimited set of role strings
        """
        role_strings = [role.strip() for role in role_description.split(",")]

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

        return sorted(roles, key=lambda r: r.value)

    def get_roles_for_application_instance(
        self, ai: ApplicationInstance, roles: list[LTIRole]
    ) -> list[Role]:
        self._db.flush()  # Make sure roles have IDs
        overrides = self._db.execute(
            select(
                LTIRole.value.label("value"),
                func.coalesce(LTIRoleOverride.type, LTIRole.type).label("type"),
                func.coalesce(LTIRoleOverride.scope, LTIRole.scope).label("scope"),
            )
            .outerjoin(LTIRoleOverride)
            .filter(
                LTIRole.id.in_([role.id for role in roles]),
                or_(
                    LTIRoleOverride.application_instance_id == ai.id,
                    LTIRoleOverride.application_instance_id.is_(None),
                ),
            )
            .order_by("value")
        )
        return [
            Role(scope=role.scope, type=role.type, value=role.value)
            for role in overrides
        ]

    def search(self, id_=None):
        query = self._db.query(LTIRole).order_by(LTIRole.value)

        if id_:
            query = query.filter(LTIRole.id == id_)

        return query

    def new_role_override(self, application_instance, role, type_, scope):
        override = LTIRoleOverride(
            application_instance=application_instance,
            lti_role=role,
            type=type_,
            scope=scope,
        )
        self._db.add(override)
        return override

    def search_override(self, id_=None):
        query = self._db.query(LTIRoleOverride)

        if id_:
            query = query.filter(LTIRoleOverride.id == id_)

        return query

    def update_override(
        self, override: LTIRoleOverride, scope, type_
    ) -> LTIRoleOverride:
        override.scope = scope
        override.type = type_

        return override

    def delete_override(self, override: LTIRoleOverride):
        self._db.delete(override)


def service_factory(_context, request) -> LTIRoleService:
    """Create an LTIRoleService object."""

    return LTIRoleService(db_session=request.db)
