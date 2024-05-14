import json
from copy import deepcopy

from sqlalchemy import Text, column, func

from lms.db import full_text_match
from lms.models import (
    ApplicationInstance,
    Course,
    CourseGroupsExportedFromH,
    Grouping,
    Organization,
)
from lms.product import Product
from lms.services.grouping import GroupingService
from lms.services.organization import OrganizationService


class CourseService:
    def __init__(
        self,
        db,
        application_instance,
        grouping_service: GroupingService,
        organization_service: OrganizationService,
    ):
        self._db = db
        self._application_instance = application_instance
        self._grouping_service = grouping_service
        self._organization_service = organization_service

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

    def get_from_launch(self, product, lti_params):
        """Get the course this LTI launch based on the request's params."""
        historical_course = None

        if existing_course := self.get_by_context_id(lti_params["context_id"]):
            # Keep existing `extra` instead of replacing it with the default
            extra = existing_course.extra
        else:
            extra = {}
            if product.family == Product.Family.CANVAS:
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
            context_id=lti_params["context_id"],
            name=lti_params["context_title"],
            extra=extra,
            copied_from=historical_course,
        )

    def search(  # pylint:disable=too-many-arguments
        self,
        id_: int | None = None,
        context_id: str | None = None,
        h_id: str | None = None,
        name: str | None = None,
        limit: int = 100,
        organization: Organization | None = None,
    ) -> list[Course]:
        query = self._db.query(Course)

        if id_:
            query = query.filter_by(id=id_)

        if context_id:
            query = query.filter_by(lms_id=context_id)

        if h_id:
            query = query.filter_by(authority_provided_id=h_id)

        if name:
            query = query.filter(full_text_match(Course.lms_name, name))

        if organization:
            organization_ids = self._organization_service.get_hierarchy_ids(
                organization.id, include_parents=False
            )
            query = (
                query.join(
                    ApplicationInstance,
                    Course.application_instance_id == ApplicationInstance.id,
                )
                .join(Organization)
                .filter(Organization.id.in_(organization_ids))
            )

        return query.limit(limit).all()

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

    def upsert_course(  # pylint:disable=too-many-arguments
        self,
        context_id,
        name,
        extra,
        settings=None,
        copied_from: Grouping | None = None,
    ) -> Course:
        """
        Create or update a course based on the provided values.

        :param context_id: The course id from LTI params
        :param name: The name of the course
        :param extra: Additional LMS specific values
        :param settings: A dict of settings for the course
        :param copied_from: A reference to the course this one was copied from
        """

        return self._grouping_service.upsert_groupings(
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
        if courses := self.search(id_=id_, limit=1):
            return courses[0]

        return None

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
        organization_service=request.find_service(OrganizationService),
    )
