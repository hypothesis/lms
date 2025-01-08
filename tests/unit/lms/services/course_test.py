from datetime import UTC, date, datetime
from unittest.mock import call, patch, sentinel

import pytest
from h_matchers import Any
from sqlalchemy.exc import NoResultFound

from lms.models import (
    ApplicationSettings,
    CourseGroupsExportedFromH,
    Grouping,
    LMSCourse,
    LMSCourseApplicationInstance,
    LMSCourseMembership,
    LTIParams,
    RoleScope,
    RoleType,
)
from lms.product.product import Product
from lms.services.course import CourseService, course_service_factory
from tests import factories


class TestCourseService:
    @pytest.mark.parametrize(
        "settings_set,value,expected",
        (
            ([], "any", False),
            ([{"group": {"key": "match"}}], "match", True),
            ([{"group": {"key": "no_match"}}], "match", False),
            (
                [{"group": {"key": "no_match"}}, {"group": {"key": "match"}}],
                "match",
                True,
            ),
        ),
    )
    def test_any_with_setting(
        self, svc, settings_set, value, expected, application_instance
    ):
        for settings in settings_set:
            factories.Course(
                application_instance=application_instance, settings=settings
            )

        # Add a matching course with a different consumer key
        factories.Course(
            application_instance=factories.ApplicationInstance(),
            settings={"group": {"key": value}},
        )

        assert svc.any_with_setting("group", "key", value) is expected

    def test_get_by_context_id(self, svc, course):
        assert svc.get_by_context_id(course.lms_id) == course

    def test_get_by_context_id_with_no_match(self, svc):
        assert svc.get_by_context_id("NO MATCH") is None

    def test_get_by_context_id_with_no_match_and_raise_on_missing(self, svc):
        with pytest.raises(NoResultFound):
            svc.get_by_context_id("NO MATCH", raise_on_missing=True)

    def test_get_from_launch_when_existing(
        self, svc, get_by_context_id, upsert_course, product, lti_params
    ):
        course = get_by_context_id.return_value = factories.Course(
            extra={"existing": "extra"}
        )

        course = svc.get_from_launch(product, lti_params=lti_params)

        get_by_context_id.assert_called_once_with(
            sentinel.context_id,
        )
        upsert_course.assert_called_once_with(
            lti_params=lti_params,
            extra={"existing": "extra"},
            copied_from=None,
        )
        assert course == upsert_course.return_value

    def test_get_from_launch_when_new(
        self, svc, get_by_context_id, upsert_course, product, lti_params
    ):
        get_by_context_id.return_value = None

        course = svc.get_from_launch(product, lti_params=lti_params)

        get_by_context_id.assert_called_once_with(sentinel.context_id)
        upsert_course.assert_called_once_with(
            lti_params=lti_params,
            extra={},
            copied_from=None,
        )
        assert course == upsert_course.return_value

    def test_get_from_launch_when_new_and_canvas(
        self, svc, upsert_course, get_by_context_id, lti_params
    ):
        get_by_context_id.return_value = None

        course = svc.get_from_launch(Product.Family.CANVAS, lti_params=lti_params)

        get_by_context_id.assert_called_once_with(sentinel.context_id)
        upsert_course.assert_called_once_with(
            lti_params=lti_params,
            extra={"canvas": {"custom_canvas_course_id": sentinel.canvas_id}},
            copied_from=None,
        )
        assert course == upsert_course.return_value

    def test_get_from_launch_when_new_and_historical_course_doesnt_exists(
        self, svc, upsert_course, product, grouping_service
    ):
        grouping_service.get_authority_provided_id.side_effect = [
            "authority_new_context_id",
            "authority_original_context_id",
        ]
        lti_params = {
            "context_id": "new_context_id",
            "context_title": sentinel.context_title,
            "custom_Context.id.history": "original_context_id",
        }

        course = svc.get_from_launch(product, lti_params=lti_params)

        upsert_course.assert_called_once_with(
            lti_params=lti_params, extra={}, copied_from=None
        )
        assert course == upsert_course.return_value

    def test_get_from_launch_when_new_and_historical_course_exists(
        self,
        svc,
        upsert_course,
        product,
        application_instance,
        grouping_service,
    ):
        grouping_service.get_authority_provided_id.side_effect = [
            "authority_new_context_id",
            "authority_original_context_id",
        ]
        lti_params = {
            "context_id": "new_context_id",
            "context_title": sentinel.context_title,
            "custom_Context.id.history": "original_context_id",
        }

        historical_course = factories.Course(
            application_instance=application_instance,
            authority_provided_id="authority_original_context_id",
            lms_id="original_context_id",
        )

        course = svc.get_from_launch(product, lti_params=lti_params)

        upsert_course.assert_called_once_with(
            lti_params=lti_params, extra={}, copied_from=historical_course
        )
        assert course == upsert_course.return_value

    @pytest.mark.parametrize(
        "custom_course_starts, course_starts_at",
        [
            (None, None),
            ("NOT A DATE", None),
            ("2022-01-01T00:00:00Z", datetime(2022, 1, 1, tzinfo=UTC)),
        ],
    )
    @pytest.mark.parametrize(
        "custom_course_ends, course_ends_at",
        [
            (None, None),
            ("NOT A DATE", None),
            ("2022-01-01T00:00:00Z", datetime(2022, 1, 1, tzinfo=UTC)),
        ],
    )
    @pytest.mark.parametrize(
        "custom_canvas_api_id",
        [None, "API ID"],
    )
    def test_upsert_course(
        self,
        svc,
        grouping_service,
        bulk_upsert,
        db_session,
        lti_params,
        custom_course_starts,
        course_starts_at,
        custom_course_ends,
        course_ends_at,
        custom_canvas_api_id,
    ):
        lti_params["custom_course_starts"] = custom_course_starts
        lti_params["custom_course_ends"] = custom_course_ends
        lti_params["custom_canvas_course_id"] = custom_canvas_api_id

        course = svc.upsert_course(
            lti_params=lti_params,
            extra=sentinel.extra,
            settings=sentinel.settings,
        )

        grouping_service.upsert_groupings.assert_called_once_with(
            [
                {
                    "lms_id": sentinel.context_id,
                    "lms_name": sentinel.context_title,
                    "extra": sentinel.extra,
                    "settings": sentinel.settings,
                }
            ],
            type_=Grouping.Type.COURSE,
            copied_from=None,
        )

        assert course == grouping_service.upsert_groupings.return_value[0]
        bulk_upsert.assert_has_calls(
            [
                call(
                    db_session,
                    LMSCourse,
                    [
                        {
                            "tool_consumer_instance_guid": course.application_instance.tool_consumer_instance_guid,
                            "lti_context_id": course.lms_id,
                            "h_authority_provided_id": course.authority_provided_id,
                            "name": course.lms_name,
                            "lti_context_memberships_url": None,
                            "starts_at": course_starts_at,
                            "ends_at": course_ends_at,
                            "lms_api_course_id": custom_canvas_api_id,
                        }
                    ],
                    index_elements=["h_authority_provided_id"],
                    update_columns=[
                        "updated",
                        "name",
                        "lti_context_memberships_url",
                        "starts_at",
                        "ends_at",
                        "lms_api_course_id",
                    ],
                ),
                call().one(),
                call(
                    db_session,
                    LMSCourseApplicationInstance,
                    [
                        {
                            "application_instance_id": course.application_instance_id,
                            "lms_course_id": bulk_upsert.return_value.one.return_value.id,
                        }
                    ],
                    index_elements=["application_instance_id", "lms_course_id"],
                    update_columns=["updated"],
                ),
            ]
        )

    @pytest.mark.parametrize("canvas_sections_enabled", [True, False])
    def test_upsert_course_sets_canvas_sections_enabled_based_on_legacy_rows(
        self,
        application_instance,
        db_session,
        svc,
        canvas_sections_enabled,
        grouping_service,
        bulk_upsert,
        lti_params,
    ):
        db_session.add(
            CourseGroupsExportedFromH(
                authority_provided_id=grouping_service.get_authority_provided_id.return_value,
                created=datetime.utcnow(),
            )
        )
        application_instance.settings = ApplicationSettings({})
        application_instance.settings.set(
            "canvas", "sections_enabled", canvas_sections_enabled
        )

        svc.upsert_course(lti_params=lti_params, extra={})

        grouping_service.upsert_groupings.assert_called_once_with(
            [
                Any.dict.containing(
                    {"settings": {"canvas": {"sections_enabled": False}}}
                )
            ],
            type_=Any(),
            copied_from=None,
        )
        bulk_upsert.assert_called()

    def test_upsert_lms_course_membership(
        self,
        db_session,
        svc,
        bulk_upsert,
    ):
        lti_roles = factories.LTIRole.create_batch(3)
        lms_user = factories.LMSUser()
        lms_course = factories.LMSCourse()
        db_session.flush()

        svc.upsert_lms_course_membership(lms_user, lms_course, lti_roles)

        bulk_upsert.assert_called_once_with(
            db_session,
            LMSCourseMembership,
            values=[
                {
                    "lms_user_id": lms_user.id,
                    "lms_course_id": lms_course.id,
                    "lti_role_id": role.id,
                }
                for role in lti_roles
            ],
            index_elements=["lms_user_id", "lms_course_id", "lti_role_id"],
            update_columns=["updated"],
        )

    @pytest.mark.parametrize(
        "param,field",
        (
            ("name", "lms_name"),
            ("context_id", "lms_id"),
            ("id_", "id"),
            ("h_id", "authority_provided_id"),
        ),
    )
    def test_search(self, svc, param, field, db_session):
        course = factories.Course(lms_name="NAME")
        # Ensure ids are written
        db_session.add(course)
        db_session.flush()

        assert svc.search(**{param: getattr(course, field)}) == [course]

    def test_search_by_organization(self, svc, db_session):
        org = factories.Organization()
        ai = factories.ApplicationInstance(organization=org)
        course = factories.Course(application_instance=ai)
        # Ensure ids are written
        db_session.flush()

        result = svc.search(organization_ids=[org.id])

        assert result == [course]

    def test_search_limit(self, svc):
        orgs = factories.Course.create_batch(10)

        result = svc.search(limit=5)

        assert len(result) == 5
        assert orgs == Any.list.containing(result)

    def test_get_by_id(self, svc, db_session):
        course = factories.Course()
        db_session.flush()

        assert course == svc.get_by_id(course.id)
        assert not svc.get_by_id(100_00)

    def test_is_member(self, svc, db_session):
        course = factories.Course()
        user = factories.User()
        other_user = factories.User()
        factories.GroupingMembership.create(grouping=course, user=user)

        db_session.flush()

        assert svc.is_member(course, user.h_userid)
        assert not svc.is_member(course, other_user.h_userid)

    def test_get_courses_deduplicates(
        self, db_session, svc, organization, application_instance
    ):
        other_ai = factories.ApplicationInstance(organization=organization)

        older_course = factories.Course(
            application_instance=other_ai,
            updated=date(2020, 2, 1),
            authority_provided_id="COURSE",
        )
        # Most recent group, same authority_provided_id, more recent update date
        course = factories.Course(
            application_instance=application_instance,
            updated=date(2022, 1, 1),
            authority_provided_id="COURSE",
        )
        db_session.flush()
        # Check that effectively there are two courses in the organization
        assert set(svc.search(organization_ids=[organization.id])) == {
            course,
            older_course,
        }

        # But organization deduplicate, We only get the most recent course
        assert db_session.scalars(
            svc.get_courses(
                admin_organization_ids=[organization.id], instructor_h_userid=None
            )
        ).all() == [course]

    def test_get_courses_by_instructor_h_userid(
        self, svc, db_session, application_instance
    ):
        factories.User()  # User not in course
        course = factories.Course(application_instance=application_instance)
        assignment = factories.Assignment()
        user = factories.User()
        lti_role = factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.INSTRUCTOR)
        factories.AssignmentMembership.create(
            assignment=assignment, user=user, lti_role=lti_role
        )
        # Other membership record, with a different role
        factories.AssignmentMembership.create(
            assignment=assignment, user=user, lti_role=factories.LTIRole()
        )
        factories.AssignmentGrouping(grouping=course, assignment=assignment)

        db_session.flush()

        assert db_session.scalars(
            svc.get_courses(instructor_h_userid=user.h_userid)
        ).all() == [course]

    def test_get_courses_by_h_userids(
        self, svc, db_session, application_instance, organization
    ):
        course = factories.Course(application_instance=application_instance)
        user = factories.User()
        factories.GroupingMembership(grouping=course, user=user)

        db_session.flush()

        assert db_session.scalars(
            svc.get_courses(
                admin_organization_ids=[organization.id], h_userids=[user.h_userid]
            )
        ).all() == [course]

    def test_get_courses_by_assignment_ids(
        self, svc, db_session, application_instance, organization
    ):
        course = factories.Course(application_instance=application_instance)
        assignment = factories.Assignment()
        user = factories.User()
        factories.AssignmentMembership.create(
            assignment=assignment, user=user, lti_role=factories.LTIRole()
        )
        factories.AssignmentGrouping(grouping=course, assignment=assignment)

        db_session.flush()

        assert db_session.scalars(
            svc.get_courses(
                admin_organization_ids=[organization.id],
                assignment_ids=[assignment.id],
            )
        ).all() == [course]

    def test_get_courses_by_course_ids(
        self, svc, db_session, application_instance, organization
    ):
        course = factories.Course(application_instance=application_instance)
        db_session.flush()

        assert db_session.scalars(
            svc.get_courses(
                admin_organization_ids=[organization.id], course_ids=[course.id]
            )
        ).all() == [course]

    @pytest.fixture
    def course(self, application_instance, grouping_service):
        return factories.Course(
            application_instance=application_instance,
            authority_provided_id=grouping_service.get_authority_provided_id.return_value,
            lms_id="context_id",
        )

    @pytest.fixture
    def application_instance(self, application_instance):
        application_instance.tool_consumer_instance_guid = "tool_consumer_instance_guid"
        return application_instance

    @pytest.fixture
    def grouping_service(self, grouping_service):
        grouping_service.get_authority_provided_id.return_value = (
            "AUTHORITY_PROVIDED_ID"
        )

        return grouping_service

    @pytest.fixture
    def svc(self, db_session, application_instance, grouping_service):
        return CourseService(
            db=db_session,
            application_instance=application_instance,
            grouping_service=grouping_service,
        )

    @pytest.fixture
    def get_by_context_id(self, svc):
        with patch.object(svc, "get_by_context_id") as get_by_context_id:
            yield get_by_context_id

    @pytest.fixture
    def upsert_course(self, svc):
        with patch.object(svc, "upsert_course") as upsert_course:
            yield upsert_course

    @pytest.fixture
    def bulk_upsert(self, patch):
        return patch("lms.services.course.bulk_upsert")

    @pytest.fixture
    def lti_params(self):
        return LTIParams(
            {
                "context_id": sentinel.context_id,
                "context_title": sentinel.context_title,
                "custom_canvas_course_id": sentinel.canvas_id,
            }
        )


class TestCourseServiceFactory:
    def test_it(self, pyramid_request, grouping_service, CourseService):
        svc = course_service_factory(sentinel.context, pyramid_request)

        CourseService.assert_called_once_with(
            db=pyramid_request.db,
            application_instance=pyramid_request.lti_user.application_instance,
            grouping_service=grouping_service,
        )

        assert svc == CourseService.return_value

    @pytest.fixture
    def CourseService(self, patch):
        return patch("lms.services.course.CourseService")
