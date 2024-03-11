import logging

from sqlalchemy.orm import Session

from lms.models import (
    Assignment,
    AssignmentGrouping,
    AssignmentMembership,
    Grouping,
    LTIRole,
    User,
)
from lms.services.upsert import bulk_upsert

LOG = logging.getLogger(__name__)


class AssignmentService:
    """A service for getting and setting assignments."""

    def __init__(self, db: Session, misc_plugin, grouping_plugin):
        self._db = db
        self._misc_plugin = misc_plugin
        self._grouping_plugin = grouping_plugin

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

    def create_assignment(self, tool_consumer_instance_guid, resource_link_id):
        """Create a new assignment."""

        assignment = Assignment(
            tool_consumer_instance_guid=tool_consumer_instance_guid,
            resource_link_id=resource_link_id,
            extra={},
        )
        self._db.add(assignment)

        return assignment

    def update_assignment(self, request, assignment, document_url, group_set_id):
        """Update an existing assignment."""

        assignment.document_url = document_url
        assignment.extra["group_set_id"] = group_set_id

        # Metadata based on the launch
        assignment.title = request.lti_params.get("resource_link_title")
        assignment.description = request.lti_params.get("resource_link_description")
        assignment.is_gradable = self._misc_plugin.is_assignment_gradable(
            request.lti_params
        )

        return assignment

    def _get_copied_from_assignment(self, lti_params) -> Assignment | None:
        """Return the assignment that the current assignment was copied from."""

        resource_link_history_params = [
            "resource_link_id_history",  # Blackboard, LTI 1.1
            "ext_d2l_resource_link_id_history",  # D2L, LTI 1.1
            "custom_ResourceLink.id.history",  # Blackboard and D2L, LTI 1.3
        ]

        for param in resource_link_history_params:
            if historical_resource_link_id := lti_params.get(param):
                # History might have a long chain of comma separated
                # copies of copies, take the most recent one.
                historical_resource_link_id = historical_resource_link_id.split(",")[0]
                if historical_assignment := self.get_assignment(
                    tool_consumer_instance_guid=lti_params.get(
                        "tool_consumer_instance_guid"
                    ),
                    resource_link_id=historical_resource_link_id,
                ):
                    return historical_assignment

        return None

    def get_assignment_for_launch(self, request) -> Assignment | None:
        """
        Get or create an assignment for the current launch.

        The returned assignment will have the relevant configuration for this
        launch.

        :returns: An assignment or None if one cannot be found or created.
        """

        lti_params = request.lti_params
        tool_consumer_instance_guid = lti_params["tool_consumer_instance_guid"]
        resource_link_id = lti_params.get("resource_link_id")

        # Get the potentially relevant assignments from the DB
        assignment = self.get_assignment(tool_consumer_instance_guid, resource_link_id)
        historical_assignment = None
        if not assignment:
            historical_assignment = self._get_copied_from_assignment(lti_params)

        # Get the configuration for the assignment
        # it might be based on the assignments we just queried or the request
        document_url = self._misc_plugin.get_document_url(
            request, assignment, historical_assignment
        )
        group_set_id = self._grouping_plugin.get_group_set_id(
            request, assignment, historical_assignment
        )

        if not document_url:
            # We can't find a document_url, we shouldn't try to create an
            # assignment yet.
            return None

        if not assignment:
            # We don't have an assignment in the DB, but we know which document
            # url it should point to. This might happen for example on:
            #
            #  * The first launch of a deep linked assignment
            #  * The first launch copied assignment
            assignment = self.create_assignment(
                tool_consumer_instance_guid, resource_link_id
            )
            # While creating a new assignment we found the assignment we
            # copied this one from. Reference this in the DB.
            assignment.copied_from = historical_assignment

            # If the request contains a DL UUID keep track of it on the DB
            assignment.deep_linking_uuid = (
                self._misc_plugin.get_deep_linked_assignment_configuration(request).get(
                    "deep_linking_uuid"
                )
            )

        # Always update the assignment configuration
        # It often will be the same one while launching the assignment again but
        # it might for example be an updated deep linked URL or similar.
        return self.update_assignment(request, assignment, document_url, group_set_id)

    def upsert_assignment_membership(
        self, assignment: Assignment, user: User, lti_roles: list[LTIRole]
    ) -> list[AssignmentMembership]:
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
        self, assignment: Assignment, groupings: list[Grouping]
    ) -> list[AssignmentGrouping]:
        """Store details of any groups and courses an assignment is in."""

        # Commit any changes to ensure that our user and role objects have ids
        self._db.flush()

        values = [
            {"assignment_id": assignment.id, "grouping_id": grouping.id}
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

    def get_by_id(self, id_: int) -> Assignment | None:
        return self._db.query(Assignment).filter_by(id=id_).one_or_none()


def factory(_context, request):
    return AssignmentService(
        db=request.db,
        misc_plugin=request.product.plugin.misc,
        grouping_plugin=request.product.plugin.grouping,
    )
