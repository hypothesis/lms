from typing import List, Optional

from sqlalchemy.orm import Session

from lms.models import (
    Assignment,
    AssignmentGrouping,
    AssignmentMembership,
    Grouping,
    LTIParams,
    LTIRole,
    User,
)
from lms.services.upsert import bulk_upsert


class AssignmentService:
    """A service for getting and setting assignments."""

    def __init__(self, db: Session):
        self._db = db

    def get_assignment(self, tool_consumer_instance_guid, resource_link_id):
        """Get an assignment by resource_link_id."""

        return (
            self._db.query(Assignment)
            .filter_by(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                resource_link_id=resource_link_id,
            )
            .one_or_none()
        )

    def get_copied_from_assignment(self, lti_params) -> Optional[Assignment]:
        """Return the assignment that the current assignment was copied from."""

        resource_link_history_params = [
            "resource_link_id_history",  # Blackboard, LTI 1.1
            "ext_d2l_resource_link_id_history",  # D2L, LTI 1.1
            "custom_ResourceLink.id.history",  # Blackboard and D2L, LTI 1.3
        ]

        for param in resource_link_history_params:
            if historical_resource_link_id := lti_params.get(param):
                if historical_assignment := self.get_assignment(
                    tool_consumer_instance_guid=lti_params.get(
                        "tool_consumer_instance_guid"
                    ),
                    resource_link_id=historical_resource_link_id,
                ):
                    return historical_assignment

        return None

    # pylint: disable=too-many-arguments
    def upsert_assignment(
        self,
        tool_consumer_instance_guid,
        resource_link_id,
        document_url,
        lti_params: LTIParams,
        is_gradable=False,
        extra=None,
    ) -> Assignment:
        """
        Update or create an assignment with the given document_url.

        Set the document_url for the assignment that matches
        tool_consumer_instance_guid and resource_link_id
        or create a new one if none exist on the DB.

        Any existing document_url for this assignment will be overwritten.


        If we detect that the new assignment in the LMS has been copied from a
        historical assignment (perhaps by using the LMS's "course copy" feature)
        then some of the new assignment's extra values might be taken from the historical assignment.
        """
        extra = extra or {}

        assignment = self.get_assignment(tool_consumer_instance_guid, resource_link_id)
        if not assignment:
            assignment = Assignment(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                document_url=document_url,
                resource_link_id=resource_link_id,
            )
            self._db.add(assignment)

            # For new assignments check if we are copying
            # from an existing one on the current launch
            historical_assignment = self.get_copied_from_assignment(lti_params)
            if (
                historical_assignment
                and historical_assignment.extra.get("group_set_id")
                and not extra.get("group_set_id")
            ):
                extra["group_set_id"] = historical_assignment.extra.get("group_set_id")

        assignment.document_url = document_url
        assignment.title = lti_params.get("resource_link_title")
        assignment.description = lti_params.get("resource_link_description")
        assignment.is_gradable = is_gradable
        if extra:
            assignment.extra = extra

        return assignment

    def upsert_assignment_membership(
        self, assignment: Assignment, user: User, lti_roles: List[LTIRole]
    ) -> List[AssignmentMembership]:
        """Store details of the roles a user plays in an assignment."""

        # Commit any changes to ensure that our user and role objects have ids
        self._db.flush()

        values = [
            {
                "user_id": user.id,
                "assignment_id": assignment.id,
                "lti_role_id": lti_role.id,
            }
            for lti_role in lti_roles
        ]

        return list(
            bulk_upsert(
                self._db,
                model_class=AssignmentMembership,
                values=values,
                index_elements=["user_id", "assignment_id", "lti_role_id"],
                update_columns=["updated"],
            )
        )

    def upsert_assignment_groupings(
        self, assignment_id, groupings: List[Grouping]
    ) -> List[AssignmentGrouping]:
        """Store details of any groups and courses an assignment is in."""

        # Commit any changes to ensure that our user and role objects have ids
        self._db.flush()

        values = [
            {"assignment_id": assignment_id, "grouping_id": grouping.id}
            for grouping in groupings
        ]

        return list(
            bulk_upsert(
                self._db,
                model_class=AssignmentGrouping,
                values=values,
                index_elements=["assignment_id", "grouping_id"],
                update_columns=["updated"],
            )
        )


def factory(_context, request):
    return AssignmentService(db=request.db)
