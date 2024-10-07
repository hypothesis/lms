import logging
from typing import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from lms.models import (
    Assignment,
    AssignmentGrouping,
    AssignmentMembership,
    AutoGradingConfig,
    Course,
    Grouping,
    LMSUser,
    LMSUserAssignmentMembership,
    LTIParams,
    LTIRole,
    User,
)
from lms.services.course import CourseService
from lms.services.upsert import bulk_upsert

LOG = logging.getLogger(__name__)


class AssignmentService:
    """A service for getting and setting assignments."""

    def __init__(self, db: Session, misc_plugin):
        self._db = db
        self._misc_plugin = misc_plugin

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

    def update_assignment(  # noqa: PLR0913, PLR0917
        self,
        request,
        assignment: Assignment,
        document_url: str,
        group_set_id,
        course: Course,
        auto_grading_config: dict | None = None,
    ):
        """Update an existing assignment."""
        if self._misc_plugin.is_speed_grader_launch(request):
            # SpeedGrader has a number of issues regarding the information it sends about the assignment
            # Don't update our DB with that nonsense.
            # See:
            #   https://github.com/instructure/canvas-lms/issues/1952
            return assignment

        assignment.document_url = document_url
        assignment.extra["group_set_id"] = group_set_id

        # Metadata based on the launch
        assignment.title = (
            request.lti_params.get("resource_link_title", "").strip() or None
        )
        assignment.description = (
            request.lti_params.get("resource_link_description", "") or None
        )
        assignment.is_gradable = self._misc_plugin.is_assignment_gradable(
            request.lti_params
        )
        # Set the value for the v13 id for this assignment.
        assignment.lti_v13_resource_link_id = request.lti_params.v13.get(
            "https://purl.imsglobal.org/spec/lti/claim/resource_link", {}
        ).get("id")

        # Keep record of the grading service URL relevant for this assignment if available
        assignment.lis_outcome_service_url = request.lti_params.get(
            "lis_outcome_service_url"
        )

        assignment.course_id = course.id
        self._update_auto_grading_config(assignment, auto_grading_config)

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

    def get_assignment_for_launch(self, request, course: Course) -> Assignment | None:
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
        assignment_config = self._misc_plugin.get_assignment_configuration(
            request, assignment, historical_assignment
        )
        document_url = assignment_config.get("document_url")
        group_set_id = assignment_config.get("group_set_id")
        auto_grading_config = assignment_config.get("auto_grading_config")

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
        return self.update_assignment(
            request, assignment, document_url, group_set_id, course, auto_grading_config
        )

    def upsert_assignment_membership(
        self,
        lti_params: LTIParams,
        assignment: Assignment,
        user: User,
        lti_roles: list[LTIRole],
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

        self._upsert_lms_user_assignment_memberships(
            lti_params, user.lms_user, assignment, lti_roles
        )

        return list(
            bulk_upsert(
                self._db,
                model_class=AssignmentMembership,
                values=values,
                index_elements=["user_id", "assignment_id", "lti_role_id"],
                update_columns=["updated"],
            )
        )

    def _upsert_lms_user_assignment_memberships(
        self,
        lti_params,
        lms_user: LMSUser,
        assignment: Assignment,
        lti_roles: list[LTIRole],
    ) -> list[LMSUserAssignmentMembership]:
        values = [
            {
                "lms_user_id": lms_user.id,
                "assignment_id": assignment.id,
                "lti_role_id": lti_role.id,
                "lti_v11_lis_result_sourcedid": None
                if lti_params.v13
                else lti_params.get("lis_result_sourcedid"),
            }
            for lti_role in lti_roles
        ]

        return list(
            bulk_upsert(
                self._db,
                model_class=LMSUserAssignmentMembership,
                values=values,
                index_elements=["lms_user_id", "assignment_id", "lti_role_id"],
                update_columns=["updated", "lti_v11_lis_result_sourcedid"],
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

    def is_member(self, assignment: Assignment, h_userid: str) -> bool:
        """Check if a user is a member of an assignment."""
        return bool(
            assignment.membership.join(User).filter(User.h_userid == h_userid).first()
        )

    def get_assignments(  # noqa: PLR0913
        self,
        instructor_h_userid: str | None = None,
        admin_organization_ids: list[int] | None = None,
        course_ids: list[int] | None = None,
        h_userids: list[str] | None = None,
        assignment_ids: list[int] | None = None,
    ) -> Select[tuple[Assignment]]:
        """Get a query to fetch assignments.

        :param instructor_h_userid: return only assignments that belong to courses where instructor_h_userid is an instructor.
        :param admin_organization_ids: organizations where the current user is an admin.
        :param course_ids: only return assignments that belong to this course.
        :param h_userids: return only assignments where these users are members.
        :param assignment_ids: return only assignments with these IDs.
        """
        candidate_courses = CourseService.courses_permission_check_query(
            instructor_h_userid, admin_organization_ids, course_ids
        ).cte("candidate_courses")

        query = (
            select(Assignment)
            .join(candidate_courses, candidate_courses.c[0] == Assignment.course_id)
            .where(Assignment.title.is_not(None))
        )

        if assignment_ids:
            query = query.where(Assignment.id.in_(assignment_ids))

        if h_userids:
            query = query.where(
                Assignment.id.in_(
                    select(AssignmentMembership.assignment_id)
                    .join(User)
                    .where(User.h_userid.in_(h_userids))
                )
            )

        return query.order_by(Assignment.title, Assignment.id)

    def get_courses_assignments_count(self, **kwargs) -> dict[int, int]:
        """Get the number of assignments a given list of courses has."""
        query = (
            # Query assignments
            self.get_assignments(**kwargs)
            # Change the selected columns
            .with_only_columns(
                Assignment.course_id,
                func.count(Assignment.id),
            )
            # Remove any sorting options, to avoid having to worry about sorted columns being or not in the select
            .order_by(None)
            # Group by course to get the counts
            .group_by(Assignment.course_id)
        )

        return {x.course_id: x.count for x in self._db.execute(query)}  # type: ignore

    def get_assignment_groups(self, assignment) -> Sequence[Grouping]:
        """Get the relevant groups for the assignment from the DB."""
        if group_set_id := assignment.extra.get("group_set_id"):
            return self._db.scalars(
                select(Grouping).where(
                    Grouping.parent_id == assignment.course_id,
                    Grouping.extra["group_set_id"].astext == str(group_set_id),
                )
            ).all()
        return []

    def get_assignment_sections(self, assignment) -> Sequence[Grouping]:
        """Get the relevant groups for the assignment from the DB."""
        return self._db.scalars(
            select(Grouping).where(
                Grouping.parent_id == assignment.course_id,
                Grouping.type == "canvas_section",
            )
        ).all()

    def _update_auto_grading_config(
        self, assignment: Assignment, auto_grading_config: dict | None
    ) -> None:
        if auto_grading_config:
            auto_grading_model = assignment.auto_grading_config
            if not assignment.auto_grading_config:
                # No existing config, create a new one
                auto_grading_model = AutoGradingConfig()
                self._db.add(auto_grading_model)
                assignment.auto_grading_config = auto_grading_model

            # Update the DB config based on the passed dict
            auto_grading_model.activity_calculation = auto_grading_config.get(
                "activity_calculation"
            )
            auto_grading_model.grading_type = auto_grading_config.get("grading_type")
            auto_grading_model.required_annotations = auto_grading_config[
                "required_annotations"
            ]
            auto_grading_model.required_replies = auto_grading_config.get(
                "required_replies"
            )
        elif assignment.auto_grading_config:
            # Clear the config in the DB when no config is passed in
            self._db.delete(assignment.auto_grading_config)
            assignment.auto_grading_config = None


def factory(_context, request):
    return AssignmentService(db=request.db, misc_plugin=request.product.plugin.misc)
