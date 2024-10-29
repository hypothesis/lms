import json
from copy import deepcopy
from typing import cast

from sqlalchemy import Select, Text, column, func, select, union

from lms.db import full_text_match
from lms.models import (
    ApplicationInstance,
    AssignmentGrouping,
    AssignmentMembership,
    Course,
    CourseGroupsExportedFromH,
    Grouping,
    GroupingMembership,
    LMSCourse,
    LMSCourseApplicationInstance,
    LMSCourseMembership,
    LMSUser,
    LTIParams,
    LTIRole,
    Organization,
    RoleScope,
    RoleType,
    User,
)
from lms.product.family import Family
from lms.services.grouping import GroupingService
from lms.services.upsert import bulk_upsert


class CourseService:
    def __init__(self, db, application_instance, grouping_service: GroupingService):
        self._db = db
        self._application_instance = application_instance
        self._grouping_service = grouping_service

    def any_with_setting(self, group, key, value=True) -> bool:
        """
        Return whether any course has the specified setting.

        Note! This will only work for courses that have the key and the value,
        so if the key is missing entirely it will not be counted.

        :param group: Setting group name
        :param key: Setting key
        :param value: Expected value
        """

        return bool(
            self._db.query(Course)
            .filter(Course.application_instance == self._application_instance)
            .filter(Course.settings[group][key] == json.dumps(value))
            .limit(1)
            .count()
        )

    def get_from_launch(self, product_family: Family, lti_params) -> Course:
        """Get the course this LTI launch based on the request's params."""
        historical_course = None

        if existing_course := self.get_by_context_id(lti_params["context_id"]):
            # Keep existing `extra` instead of replacing it with the default
            extra = existing_course.extra
        else:
            extra = {}
            if product_family == Family.CANVAS:
                extra = {
                    "canvas": {
                        "custom_canvas_course_id": lti_params.get(
                            "custom_canvas_course_id"
                        )
                    }
                }
            # Only make the query for the original course for new courses
            historical_course = self._get_copied_from_course(lti_params)

        return self.upsert_course(
            lti_params=lti_params,
            extra=extra,
            copied_from=historical_course,
        )

    def _search_query(  # noqa: PLR0913, PLR0917
        self,
        id_: int | None = None,
        context_id: str | None = None,
        h_id: str | None = None,
        name: str | None = None,
        limit: int | None = 100,
        organization_ids: list[int] | None = None,
    ):
        query = self._db.query(Course)

        if id_:
            query = query.filter_by(id=id_)

        if context_id:
            query = query.filter_by(lms_id=context_id)

        if h_id:
            query = query.filter_by(authority_provided_id=h_id)

        if name:
            query = query.filter(full_text_match(Course.lms_name, name))

        if organization_ids:
            query = (
                query.join(
                    ApplicationInstance,
                    Course.application_instance_id == ApplicationInstance.id,
                )
                .join(Organization)
                .filter(Organization.id.in_(organization_ids))
            )

        return query.limit(limit)

    def search(  # noqa: PLR0913, PLR0917
        self,
        id_: int | None = None,
        context_id: str | None = None,
        h_id: str | None = None,
        name: str | None = None,
        limit: int | None = 100,
        organization_ids: list[int] | None = None,
    ) -> list[Course]:
        return self._search_query(
            id_=id_,
            context_id=context_id,
            h_id=h_id,
            name=name,
            limit=limit,
            organization_ids=organization_ids,
        ).all()

    def get_courses(  # noqa: PLR0913
        self,
        instructor_h_userid: str | None = None,
        admin_organization_ids: list[int] | None = None,
        h_userids: list[str] | None = None,
        assignment_ids: list[int] | None = None,
        course_ids: list[int] | None = None,
    ) -> Select[tuple[Course]]:
        """Get a list of unique courses.

        :param admin_organization_ids: organizations where the current user is an admin.
        :param instructor_h_userid: return only courses where instructor_h_userid is an instructor.
        :param h_userids: return only courses where these users are members.
        :param assignment_ids: return only the courses these assignments belong to.
        :param course_ids: return only courses with these IDs.
        """
        candidate_courses = CourseService.courses_permission_check_query(
            instructor_h_userid, admin_organization_ids, course_ids
        ).cte("candidate_courses")

        query = (
            select(Course.id)
            # Deduplicate courses by authority_provided_id, take the last updated one
            .distinct(Course.authority_provided_id)
            .join(candidate_courses, candidate_courses.c[0] == Course.id)
            .order_by(Course.authority_provided_id, Course.updated.desc())
        )

        if assignment_ids:
            query = query.where(
                Course.id.in_(
                    select(AssignmentGrouping.grouping_id).where(
                        AssignmentGrouping.assignment_id.in_(assignment_ids)
                    )
                )
            )

        if h_userids:
            query = query.where(
                Course.id.in_(
                    select(GroupingMembership.grouping_id)
                    .join(User)
                    .where(User.h_userid.in_(h_userids))
                )
            )

        return (
            select(Course)
            .where(Course.id.in_(query))
            # We can sort these again without affecting deduplication
            .order_by(Course.lms_name, Course.id)
        )

    @staticmethod
    def courses_permission_check_query(
        instructor_h_userid: str | None = None,
        admin_organization_ids: list[int] | None = None,
        course_ids: list[int] | None = None,
    ):
        courses_where_instructor_query = select(None)  # type: ignore
        courses_where_admin_query = select(None)  # type: ignore

        if instructor_h_userid:
            # Get all the courses where instructor_h_userid is an instructor. This will query AssignmentMembership, which includes roles
            courses_where_instructor_query = CourseService._course_ids_with_role_query(
                instructor_h_userid, RoleScope.COURSE, RoleType.INSTRUCTOR
            )

            if course_ids:
                courses_where_instructor_query = courses_where_instructor_query.where(
                    AssignmentGrouping.grouping_id.in_(course_ids)
                )

        if admin_organization_ids:
            # Also get all the courses of organiations where this users is an admin
            courses_where_admin_query = (
                select(Course.id)
                .join(ApplicationInstance)
                .where(
                    ApplicationInstance.organization_id.in_(admin_organization_ids),
                )
            )

            if course_ids:
                courses_where_admin_query = courses_where_admin_query.where(
                    Course.id.in_(course_ids)
                )

        return union(
            courses_where_admin_query,
            courses_where_instructor_query,
        )

    @staticmethod
    def _course_ids_with_role_query(
        h_userid: str, role_scope, role_type
    ) -> Select[tuple[int]]:
        """Return a query that returns all the Course.id where h_userid belongs as (role_scope, role_type)."""
        return (
            select(AssignmentGrouping.grouping_id)
            .join(
                # GroupingMembership doesn't contain role information.
                # We only record membership information with roles in AssignmentMembership even if that
                # information is scoped to the Course in the LTI context.
                AssignmentMembership,
                AssignmentMembership.assignment_id == AssignmentGrouping.assignment_id,
            )
            .join(User)
            .join(LTIRole)
            .where(
                User.h_userid == h_userid,
                LTIRole.scope == role_scope,
                LTIRole.type == role_type,
            )
        )

    def get_by_context_id(self, context_id, raise_on_missing=False) -> Course | None:
        """
        Get a course (if one exists) by the GUID and context id.

        :param context_id: The course id from LTI params
        :param raise_on_missing: Raise instead of returning None when no match can be found.

        :raises: sqlalchemy.exc.NoResultFound when `raise_on_missing`=True and no matching course can be found.
        """
        query = self._db.query(Course).filter_by(
            application_instance=self._application_instance,
            authority_provided_id=self._get_authority_provided_id(context_id),
        )

        if raise_on_missing:
            return query.one()

        return query.one_or_none()

    def upsert_course(
        self,
        lti_params: LTIParams,
        extra: dict,
        settings=None,
        copied_from: Grouping | None = None,
    ) -> Course:
        """
        Create or update a course based on the provided values.

        :param lti_params: Parameters from the LTI launch
        :param extra: Additional LMS specific values
        :param settings: A dict of settings for the course
        :param copied_from: A reference to the course this one was copied from
        """

        context_id = lti_params["context_id"]
        name = lti_params["context_title"]

        course = self._grouping_service.upsert_groupings(
            [
                {
                    "lms_id": context_id,
                    "lms_name": name,
                    "extra": extra,
                    "settings": settings or self._new_course_settings(context_id),
                }
            ],
            type_=Grouping.Type.COURSE,
            copied_from=copied_from,
        )[0]
        # upsert_groupings returns Groupings of type `type_`
        course = cast(Course, course)

        self._upsert_lms_course(course, lti_params)
        return course

    def _upsert_lms_course(self, course: Course, lti_params: LTIParams) -> LMSCourse:
        """Upsert LMSCourse based on a Course object."""
        self._db.flush()  # Make sure Course has hit the DB on the current transaction

        lti_context_membership_url = lti_params.v13.get(
            "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice", {}
        ).get("context_memberships_url")

        lms_course = bulk_upsert(
            self._db,
            LMSCourse,
            [
                {
                    "tool_consumer_instance_guid": course.application_instance.tool_consumer_instance_guid,
                    "lti_context_id": course.lms_id,
                    "h_authority_provided_id": course.authority_provided_id,
                    "name": course.lms_name,
                    "lti_context_memberships_url": lti_context_membership_url,
                }
            ],
            index_elements=["h_authority_provided_id"],
            update_columns=["updated", "name", "lti_context_memberships_url"],
        ).one()
        bulk_upsert(
            self._db,
            LMSCourseApplicationInstance,
            [
                {
                    "application_instance_id": course.application_instance_id,
                    "lms_course_id": lms_course.id,
                }
            ],
            index_elements=["application_instance_id", "lms_course_id"],
            update_columns=["updated"],
        )
        return lms_course

    def upsert_lms_course_membership(
        self, lms_user: LMSUser, lms_course: LMSCourse, lti_roles: list[LTIRole]
    ):
        values = [
            {
                "lms_user_id": lms_user.id,
                "lms_course_id": lms_course.id,
                "lti_role_id": lti_role.id,
            }
            for lti_role in lti_roles
        ]

        return list(
            bulk_upsert(
                self._db,
                model_class=LMSCourseMembership,
                values=values,
                index_elements=["lms_user_id", "lms_course_id", "lti_role_id"],
                update_columns=["updated"],
            )
        )

    def find_group_set(self, group_set_id=None, name=None, context_id=None):
        """
        Find the first matching group set in this course.

        Group sets are stored as part of Course.extra, this method allows to query and filter them.

        :param context_id: Match only group sets of courses with this ID
        :param name: Filter courses by name
        :param group_set_id: Filter courses by ID
        """
        group_set = (
            func.jsonb_to_recordset(Course.extra["group_sets"])
            .table_valued(
                column("id", Text), column("name", Text), joins_implicitly=True
            )
            .render_derived(with_types=True)
        )

        query = self._db.query(Grouping.id, group_set.c.id, group_set.c.name).filter(
            Grouping.application_instance == self._application_instance
        )

        if context_id:
            query = query.filter(Grouping.lms_id == context_id)

        if group_set_id:
            query = query.filter(group_set.c.id == group_set_id)

        if name:
            query = query.filter(
                func.lower(func.trim(group_set.c.name)) == func.lower(func.trim(name))
            )

        if group_set := query.first():
            return {"id": group_set.id, "name": group_set.name}

        return None

    def get_by_id(self, id_: int) -> Course | None:
        return self._search_query(id_=id_).one_or_none()

    def is_member(self, course: Course, h_userid: str) -> bool:
        """Check if an H user is a member of a course."""
        return bool(
            course.memberships.join(User).filter(User.h_userid == h_userid).first()
        )

    def _get_authority_provided_id(self, context_id):
        return self._grouping_service.get_authority_provided_id(
            lms_id=context_id, type_=Grouping.Type.COURSE
        )

    def _new_course_settings(self, context_id):
        # By default we'll make our course setting have the same settings
        # as the application instance
        course_settings = deepcopy(self._application_instance.settings)

        # Unless! The group was pre-sections, and we've just seen it for the
        # first time in which case turn sections off
        if course_settings.get("canvas", "sections_enabled") and self._is_pre_sections(
            context_id
        ):
            course_settings.set("canvas", "sections_enabled", False)

        return course_settings

    def _is_pre_sections(self, context_id):
        return bool(
            self._db.get(
                CourseGroupsExportedFromH, self._get_authority_provided_id(context_id)
            )
        )

    def _get_copied_from_course(self, lti_params) -> Course | None:
        """Return the course that the current one was copied from."""

        history_params = [
            "custom_Context.id.history",  # LTI 1.3
            "custom_context_id_history",  # LTI 1.1
        ]

        for param in history_params:
            if historical_context_id := lti_params.get(param):
                # History might have a long chain of comma separated
                # copies of copies, take the most recent one.
                historical_context_id = historical_context_id.split(",")[0]
                if historical_course := self.get_by_context_id(historical_context_id):
                    return historical_course

        return None


def course_service_factory(_context, request):
    return CourseService(
        db=request.db,
        application_instance=(
            request.lti_user.application_instance if request.lti_user else None
        ),
        grouping_service=request.find_service(name="grouping"),
    )
