from datetime import date, datetime
from unittest.mock import patch, sentinel

import pytest
from h_matchers import Any
from sqlalchemy.exc import NoResultFound

from lms.models import (
    ApplicationSettings,
    CourseGroupsExportedFromH,
    Grouping,
    RoleScope,
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
        self, svc, get_by_context_id, upsert_course, product
    ):
        course = get_by_context_id.return_value = factories.Course(
            extra={"existing": "extra"}
        )

        course = svc.get_from_launch(
            product,
            lti_params={
                "context_id": sentinel.context_id,
                "context_title": sentinel.context_title,
            },
        )

        get_by_context_id.assert_called_once_with(
            sentinel.context_id,
        )
        upsert_course.assert_called_once_with(
            context_id=sentinel.context_id,
            name=sentinel.context_title,
            extra={"existing": "extra"},
            copied_from=None,
        )
        assert course == upsert_course.return_value

    def test_get_from_launch_when_new(
        self, svc, get_by_context_id, upsert_course, product
    ):
        get_by_context_id.return_value = None

        course = svc.get_from_launch(
            product,
            lti_params={
                "context_id": sentinel.context_id,
                "context_title": sentinel.context_title,
            },
        )

        get_by_context_id.assert_called_once_with(sentinel.context_id)
        upsert_course.assert_called_once_with(
            context_id=sentinel.context_id,
            name=sentinel.context_title,
            extra={},
            copied_from=None,
        )
        assert course == upsert_course.return_value

    def test_get_from_launch_when_new_and_canvas(
        self, svc, upsert_course, get_by_context_id, product
    ):
        get_by_context_id.return_value = None
        product.family = Product.Family.CANVAS

        course = svc.get_from_launch(
            product,
            lti_params={
                "context_id": sentinel.context_id,
                "context_title": sentinel.context_title,
                "custom_canvas_course_id": sentinel.canvas_id,
            },
        )

        get_by_context_id.assert_called_once_with(sentinel.context_id)
        upsert_course.assert_called_once_with(
            context_id=sentinel.context_id,
            name=sentinel.context_title,
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

        course = svc.get_from_launch(
            product,
            lti_params={
                "context_id": "new_context_id",
                "context_title": sentinel.context_title,
                "custom_Context.id.history": "original_context_id",
            },
        )

        upsert_course.assert_called_once_with(
            context_id="new_context_id",
            name=sentinel.context_title,
            extra={},
            copied_from=None,
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

        historical_course = factories.Course(
            application_instance=application_instance,
            authority_provided_id="authority_original_context_id",
            lms_id="original_context_id",
        )

        course = svc.get_from_launch(
            product,
            lti_params={
                "context_id": "new_context_id",
                "context_title": sentinel.context_title,
                "custom_Context.id.history": "original_context_id",
            },
        )

        upsert_course.assert_called_once_with(
            context_id="new_context_id",
            name=sentinel.context_title,
            extra={},
            copied_from=historical_course,
        )
        assert course == upsert_course.return_value

    def test_upsert_course(self, svc, grouping_service):
        course = svc.upsert_course(
            context_id=sentinel.context_id,
            name=sentinel.name,
            extra=sentinel.extra,
            settings=sentinel.settings,
        )

        grouping_service.upsert_groupings.assert_called_once_with(
            [
                {
                    "lms_id": sentinel.context_id,
                    "lms_name": sentinel.name,
                    "extra": sentinel.extra,
                    "settings": sentinel.settings,
                }
            ],
            type_=Grouping.Type.COURSE,
            copied_from=None,
        )

        assert course == grouping_service.upsert_groupings.return_value[0]

    @pytest.mark.parametrize("canvas_sections_enabled", [True, False])
    def test_upsert_course_sets_canvas_sections_enabled_based_on_legacy_rows(
        self,
        application_instance,
        db_session,
        svc,
        canvas_sections_enabled,
        grouping_service,
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

        svc.upsert_course("context_id", "new course name", {})

        grouping_service.upsert_groupings.assert_called_once_with(
            [
                Any.dict.containing(
                    {"settings": {"canvas": {"sections_enabled": False}}}
                )
            ],
            type_=Any(),
            copied_from=None,
        )

    @pytest.mark.usefixtures("course_with_group_sets")
    @pytest.mark.parametrize(
        "params",
        (
            {"context_id": "context_id", "group_set_id": "ID", "name": "NAME"},
            {"context_id": "context_id", "name": "NAME"},
            {"context_id": "context_id", "name": "name"},
            {"context_id": "context_id", "name": "NAME    "},
            {"context_id": "context_id", "group_set_id": "ID"},
        ),
    )
    def test_find_group_set(self, svc, params):
        group_set = svc.find_group_set(**params)

        assert group_set["id"] == "ID"
        assert group_set["name"] == "NAME"

    @pytest.mark.usefixtures("course_with_group_sets")
    @pytest.mark.parametrize(
        "params",
        (
            {"context_id": "context_id", "group_set_id": "NOID", "name": "NAME"},
            {"context_id": "context_id", "group_set_id": "ID", "name": "NONAME"},
            {"context_id": "no_context_id", "group_set_id": "ID", "name": "NAME"},
        ),
    )
    def test_find_group_set_no_matches(self, svc, params):
        assert not svc.find_group_set(**params)

    @pytest.mark.usefixtures("course_with_group_sets")
    def test_find_group_set_returns_first_result(self, svc):
        assert svc.find_group_set()

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

    def test_search_by_h_userid(self, svc, db_session):
        user = factories.User()
        course = factories.Course()
        assignment = factories.Assignment()
        factories.Course.create_batch(10)
        factories.AssignmentGrouping(grouping=course, assignment=assignment)
        factories.AssignmentMembership(
            assignment=assignment, user=user, lti_role=factories.LTIRole()
        )
        # Ensure ids are written
        db_session.flush()

        result = svc.search(h_userid=user.h_userid)

        assert result == [course]

    def test_search_by_h_userid_and_role(self, svc, db_session):
        user = factories.User()
        course = factories.Course()
        lti_role = factories.LTIRole()
        assignment = factories.Assignment()
        factories.Course.create_batch(10)
        factories.AssignmentGrouping(grouping=course, assignment=assignment)
        factories.AssignmentMembership(
            assignment=assignment, user=user, lti_role=lti_role
        )
        # Ensure ids are written
        db_session.flush()

        result = svc.search(
            h_userid=user.h_userid, role_scope=lti_role.scope, role_type=lti_role.type
        )

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

    def test_get_members(self, svc, db_session):
        factories.User()  # User not in assignment
        assignment = factories.Assignment()
        user = factories.User()
        course = factories.Course()
        lti_role = factories.LTIRole(scope=RoleScope.COURSE)
        factories.AssignmentMembership.create(
            assignment=assignment, user=user, lti_role=lti_role
        )
        # User in assignment with other role
        factories.AssignmentMembership.create(
            assignment=assignment,
            user=factories.User(),
            lti_role=factories.LTIRole(scope=RoleScope.SYSTEM),
        )
        factories.AssignmentGrouping(grouping=course, assignment=assignment)

        db_session.flush()

        assert svc.get_members(
            course, role_scope=lti_role.scope, role_type=lti_role.type
        ) == [user]

    def test_get_organization_courses_deduplicates(self, db_session, svc):
        org = factories.Organization()

        ai = factories.ApplicationInstance(organization=org)
        other_ai = factories.ApplicationInstance(organization=org)

        older_course = factories.Course(
            application_instance=other_ai,
            updated=date(2020, 2, 1),
            authority_provided_id="COURSE",
        )
        # Most recent group, same authority_provided_id, more recent update date
        course = factories.Course(
            application_instance=ai,
            updated=date(2022, 1, 1),
            authority_provided_id="COURSE",
        )
        db_session.flush()
        # Check that effectively there are two courses in the organization
        assert set(svc.search(organization_ids=[org.id])) == {course, older_course}

        # But organization deduplicate, We only get the most recent course
        assert svc.get_organization_courses(org, None) == [course]

    def test_get_assignments(self, db_session, svc):
        course = factories.Course()
        other_course = factories.Course()

        assignment = factories.Assignment()

        # other course only has an assignment that `course` has stolen
        factories.AssignmentGrouping(
            grouping=other_course, assignment=assignment, updated=date(2020, 1, 1)
        )
        factories.AssignmentGrouping(
            grouping=course, assignment=assignment, updated=date(2022, 1, 1)
        )
        db_session.flush()

        assert svc.get_assignments(course) == [assignment]
        # While we don't expect to get the other one at all, now the assignment belongs to the most recent course
        assert not svc.get_assignments(other_course)

    def test_get_assignments_filter_by_h_userid(self, db_session, svc):
        user = factories.User(h_userid="H_USERID")
        course = factories.Course()

        assignment = factories.Assignment()
        other_assignment = factories.Assignment()

        factories.AssignmentGrouping(grouping=course, assignment=assignment)
        factories.AssignmentMembership(
            assignment=assignment, user=user, lti_role=factories.LTIRole()
        )
        # Assignment user doesn't belong to
        factories.AssignmentGrouping(grouping=course, assignment=other_assignment)
        db_session.flush()

        assert not svc.get_assignments(course, "SOME_OTHER_H_USERID")
        assert svc.get_assignments(course, user.h_userid) == [assignment]

    def test_get_courses_assignments_count(self, svc, db_session):
        course = factories.Course()
        other_course = factories.Course()

        assignment = factories.Assignment()

        # other course only has an assignment that `course` has stolen
        factories.AssignmentGrouping(
            grouping=other_course, assignment=assignment, updated=date(2020, 1, 1)
        )
        factories.AssignmentGrouping(
            grouping=course, assignment=assignment, updated=date(2022, 1, 1)
        )
        db_session.flush()

        assert svc.get_courses_assignments_count([course, other_course]) == {
            course.id: 1
        }

    @pytest.fixture
    def course(self, application_instance, grouping_service):
        return factories.Course(
            application_instance=application_instance,
            authority_provided_id=grouping_service.get_authority_provided_id.return_value,
            lms_id="context_id",
        )

    @pytest.fixture
    def course_with_group_sets(self, course):
        course.extra = {
            "group_sets": [
                {
                    "id": "ID",
                    "name": "NAME",
                },
                {
                    "id": "NOT MATCHING ID NOISE",
                    "name": "NOT MATCHING NAME NOISE",
                },
            ]
        }
        return course

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
