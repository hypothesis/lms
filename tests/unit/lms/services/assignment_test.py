from datetime import datetime
from unittest.mock import patch, sentinel

import pytest
from h_matchers import Any

from lms.models import (
    AssignmentGrouping,
    AssignmentMembership,
    AutoGradingConfig,
    RoleScope,
    RoleType,
)
from lms.services.assignment import AssignmentService, factory
from tests import factories


class TestAssignmentService:
    def test_get_assignment(self, svc, assignment, matching_params):
        assert svc.get_assignment(**matching_params) == assignment

    def test_get_assignment_without_match(self, svc, non_matching_params):
        assert svc.get_assignment(**non_matching_params) is None

    def test_create_assignment(self, svc, db_session):
        assignment = svc.create_assignment(sentinel.guid, sentinel.resource_link_id)

        assert assignment.tool_consumer_instance_guid == sentinel.guid
        assert assignment.resource_link_id == sentinel.resource_link_id
        assert assignment.extra == {}

        assert assignment in db_session.new

    @pytest.mark.parametrize("is_speed_grader", [False, True])
    @pytest.mark.parametrize(
        "resource_link_title, title",
        [("", None), ("    ", None), (" title  ", "title")],
    )
    def test_update_assignment(
        self,
        svc,
        pyramid_request,
        is_speed_grader,
        misc_plugin,
        resource_link_title,
        title,
        course,
    ):
        pyramid_request.lti_params["resource_link_title"] = resource_link_title
        misc_plugin.is_speed_grader_launch.return_value = is_speed_grader

        assignment = svc.update_assignment(
            pyramid_request,
            factories.Assignment(),
            sentinel.document_url,
            sentinel.group_set_id,
            course,
        )

        if is_speed_grader:
            assert assignment.extra == {}
            assert assignment.document_url != sentinel.document_url
        else:
            assert assignment.document_url == sentinel.document_url
            assert assignment.extra["group_set_id"] == sentinel.group_set_id
            assert assignment.title == title
            assert assignment.course_id == course.id

    def test_update_assignment_updates_auto_grading_config(
        self,
        svc,
        pyramid_request,
        course,
    ):
        assignment = factories.Assignment(
            auto_grading_config=AutoGradingConfig(
                activity_calculation="separate",
                grading_type="scaled",
                required_annotations=1,
                required_replies=1,
            )
        )

        assignment = svc.update_assignment(
            pyramid_request,
            assignment,
            sentinel.document_url,
            sentinel.group_set_id,
            course,
            auto_grading_config={
                "activity_calculation": "combined",
                "grading_type": "all_or_nothing",
                "required_annotations": 10,
                "required_replies": 10,
            },
        )

        assert assignment.auto_grading_config.activity_calculation == "combined"
        assert assignment.auto_grading_config.grading_type == "all_or_nothing"
        assert assignment.auto_grading_config.required_annotations == 10
        assert assignment.auto_grading_config.required_replies == 10

    @pytest.mark.parametrize(
        "param",
        (
            "resource_link_id_history",
            "ext_d2l_resource_link_id_history",
            "custom_ResourceLink.id.history",
        ),
    )
    def test__get_copied_from_assignment(self, svc, param, assignment):
        assert (
            svc._get_copied_from_assignment(  # noqa: SLF001
                {
                    param: assignment.resource_link_id,
                    "tool_consumer_instance_guid": assignment.tool_consumer_instance_guid,
                }
            )
            == assignment
        )

    def test__get_copied_from_assignment_not_found_bad_parameter(self, svc, assignment):
        assert not svc._get_copied_from_assignment(  # noqa: SLF001
            {
                "unknown_param": assignment.resource_link_id,
                "tool_consumer_instance_guid": assignment.tool_consumer_instance_guid,
            }
        )

    def test__get_copied_from_assignment_not_found(self, svc, assignment):
        assert not svc._get_copied_from_assignment(  # noqa: SLF001
            {
                "resource_link_id_history": "Unknown_RESOURCE_LINK_ID",
                "tool_consumer_instance_guid": assignment.tool_consumer_instance_guid,
            }
        )

    def test_get_assignment_for_launch_existing(
        self,
        pyramid_request,
        svc,
        misc_plugin,
        get_assignment,
        _get_copied_from_assignment,
        course,
    ):
        misc_plugin.get_assignment_configuration.return_value = {
            "document_url": sentinel.document_url,
            "group_set_id": sentinel.group_set_id,
        }
        get_assignment.return_value = factories.Assignment()

        assignment = svc.get_assignment_for_launch(pyramid_request, course)

        _get_copied_from_assignment.assert_not_called()
        misc_plugin.get_assignment_configuration.assert_called_once_with(
            pyramid_request, get_assignment.return_value, None
        )
        misc_plugin.is_assignment_gradable.assert_called_once_with(
            pyramid_request.lti_params
        )
        assert assignment.document_url == sentinel.document_url
        assert assignment.extra["group_set_id"] == sentinel.group_set_id

        assert assignment.title == pyramid_request.lti_params.get("resource_link_title")
        assert assignment.description == pyramid_request.lti_params.get(
            "resource_link_description"
        )
        assert assignment.is_gradable == misc_plugin.is_assignment_gradable.return_value
        assert assignment.course_id == course.id
        assert assignment.lis_outcome_service_url == "GRADING URL"

    def test_get_assignment_for_launch_set_v13_context_id(
        self, lti_v13_pyramid_request, svc, course
    ):
        assignment = svc.get_assignment_for_launch(lti_v13_pyramid_request, course)

        assert assignment.lti_v13_resource_link_id == "RESOURCE_LINK_ID"

    def test_get_assignment_returns_None_with_when_no_document(
        self, pyramid_request, svc, misc_plugin, course
    ):
        misc_plugin.get_assignment_configuration.return_value = {"document_url": None}

        assert not svc.get_assignment_for_launch(pyramid_request, course)

    @pytest.mark.parametrize("group_set_id", [None, "1"])
    def test_get_assignment_creates_assignment(
        self,
        pyramid_request,
        svc,
        misc_plugin,
        get_assignment,
        _get_copied_from_assignment,
        create_assignment,
        group_set_id,
        course,
    ):
        misc_plugin.get_assignment_configuration.return_value = {
            "document_url": sentinel.document_url,
            "group_set_id": group_set_id,
        }
        create_assignment.return_value = factories.Assignment()
        get_assignment.return_value = None
        _get_copied_from_assignment.return_value = None

        assignment = svc.get_assignment_for_launch(pyramid_request, course)

        _get_copied_from_assignment.assert_called_once_with(pyramid_request.lti_params)
        create_assignment.assert_called_once_with(
            "TEST_TOOL_CONSUMER_INSTANCE_GUID", "TEST_RESOURCE_LINK_ID"
        )
        assert assignment.document_url == sentinel.document_url
        assert assignment.course_id == course.id
        if group_set_id:
            assignment.extra["group_set_id"] = group_set_id
        assert not assignment.copied_from

    def test_get_assignment_created_assignments_point_to_copy(
        self,
        pyramid_request,
        svc,
        misc_plugin,
        get_assignment,
        _get_copied_from_assignment,
        create_assignment,
        course,
    ):
        misc_plugin.get_assignment_configuration.return_value = {
            "document_url": sentinel.document_url
        }
        get_assignment.return_value = None
        _get_copied_from_assignment.return_value = sentinel.original_assignment

        assignment = svc.get_assignment_for_launch(pyramid_request, course)

        _get_copied_from_assignment.assert_called_once_with(pyramid_request.lti_params)
        create_assignment.assert_called_once_with(
            "TEST_TOOL_CONSUMER_INSTANCE_GUID", "TEST_RESOURCE_LINK_ID"
        )
        assert assignment.copied_from == sentinel.original_assignment
        assert assignment.document_url == sentinel.document_url

    def test_upsert_assignment_membership(self, svc, assignment):
        user = factories.User()
        lti_roles = factories.LTIRole.create_batch(3)
        # One existing row
        factories.AssignmentMembership.create(
            assignment=assignment, user=user, lti_role=lti_roles[0]
        )

        membership = svc.upsert_assignment_membership(
            assignment=assignment, user=user, lti_roles=lti_roles
        )
        assert (
            membership
            == Any.list.containing(
                [
                    Any.instance_of(AssignmentMembership).with_attrs(
                        {"user": user, "assignment": assignment, "lti_role": lti_role}
                    )
                    for lti_role in lti_roles
                ]
            ).only()
        )

    def test_upsert_assignment_grouping(self, svc, assignment, db_session):
        groupings = factories.CanvasGroup.create_batch(3)
        # One existing row
        factories.AssignmentGrouping.create(
            assignment=assignment, grouping=groupings[0]
        )
        db_session.flush()

        refs = svc.upsert_assignment_groupings(assignment, groupings)

        assert refs == Any.list.containing(
            [
                Any.instance_of(AssignmentGrouping).with_attrs(
                    {"assignment": assignment, "grouping": grouping}
                )
                for grouping in groupings
            ]
        )

    def test_get_by_id(self, svc, db_session):
        assignment = factories.Assignment()
        db_session.flush()

        assert assignment == svc.get_by_id(assignment.id)

    def test_is_member(self, svc, db_session):
        assignment = factories.Assignment()
        user = factories.User()
        other_user = factories.User()
        lti_role_1 = factories.LTIRole()
        lti_role_2 = factories.LTIRole()
        factories.AssignmentMembership.create(
            assignment=assignment, user=user, lti_role=lti_role_1
        )
        factories.AssignmentMembership.create(
            assignment=assignment, user=user, lti_role=lti_role_2
        )

        db_session.flush()

        assert svc.is_member(assignment, user.h_userid)
        assert not svc.is_member(assignment, other_user.h_userid)

    @pytest.mark.parametrize("instructor_h_userid", [True, False])
    @pytest.mark.parametrize("course_ids", [True, False])
    @pytest.mark.parametrize("h_userids", [True, False])
    @pytest.mark.parametrize("assignment_ids", [True, False])
    @pytest.mark.parametrize("with_empty_title", [True, False])
    def test_get_assignments(
        self,
        svc,
        db_session,
        instructor_h_userid,
        assignment,
        course_ids,
        h_userids,
        assignment_ids,
        organization,
        course,
        instructor_in_assignment,
        with_empty_title,
    ):
        if with_empty_title:
            assignment.title = None
        factories.User()
        assignment.course = course
        factories.AssignmentGrouping(grouping=course, assignment=assignment)
        db_session.flush()

        query_parameters = {}

        if instructor_h_userid:
            query_parameters["instructor_h_userid"] = instructor_in_assignment.h_userid
        else:
            query_parameters["admin_organization_ids"] = [organization.id]

        if course_ids:
            query_parameters["course_ids"] = [course.id]

        if h_userids:
            query_parameters["h_userids"] = [instructor_in_assignment.h_userid]
        if assignment_ids:
            query_parameters["assignment_ids"] = [assignment.id]

        query = svc.get_assignments(**query_parameters)

        if with_empty_title:
            assert not db_session.scalars(query).all()
        else:
            assert db_session.scalars(query).all() == [assignment]

    def test_get_assignments_returns_all_assignments_for_instructor(
        self, db_session, svc, assignment, instructor_in_assignment, course
    ):
        # assignment belongs to course and we have membership via `instructor_in_assignment`
        assignment.course = course
        factories.AssignmentGrouping(assignment=assignment, grouping=course)

        # Assignment that belongs to the same course but for which we don't have a AssignmentMembership row
        assignment_not_launched_by_instructor = factories.Assignment(
            course=assignment.course
        )
        db_session.flush()

        assert set(
            db_session.scalars(
                svc.get_assignments(
                    instructor_h_userid=instructor_in_assignment.h_userid
                )
            ).all()
        ) == {assignment, assignment_not_launched_by_instructor}

    def test_get_courses_assignments_count(
        self, svc, db_session, organization, course, application_instance
    ):
        factories.Assignment(course=course)
        factories.Assignment(course=course)
        factories.Assignment(course=course)

        other_course = factories.Course(application_instance=application_instance)
        factories.Assignment(course=other_course)

        db_session.flush()

        assert svc.get_courses_assignments_count(
            course_ids=[course.id, other_course.id],
            admin_organization_ids=[organization.id],
        ) == {course.id: 3, other_course.id: 1}

    def test_get_assignment_groups(self, svc, db_session, course):
        assignment = factories.Assignment(course=course, extra={"group_set_id": 1})
        group = factories.CanvasGroup(parent=course, extra={"group_set_id": 1})
        db_session.flush()

        assert svc.get_assignment_groups(assignment) == [group]

    def test_get_assignment_groups_when_no_groups_used(self, svc, db_session, course):
        assignment = factories.Assignment(course=course)
        db_session.flush()

        assert not svc.get_assignment_groups(assignment)

    def test_get_assignment_sections(self, svc, db_session, course):
        assignment = factories.Assignment(course=course)
        section = factories.CanvasSection(parent=course)
        db_session.flush()

        assert svc.get_assignment_sections(assignment) == [section]

    @pytest.fixture
    def svc(self, db_session, misc_plugin):
        return AssignmentService(db_session, misc_plugin)

    @pytest.fixture(autouse=True)
    def assignment(self):
        return factories.Assignment(
            created=datetime(2000, 1, 1), updated=datetime(2000, 1, 1)
        )

    @pytest.fixture()
    def instructor_in_assignment(self, assignment):
        user = factories.User()
        lti_role = factories.LTIRole(scope=RoleScope.COURSE, type=RoleType.INSTRUCTOR)
        factories.AssignmentMembership.create(
            assignment=assignment, user=user, lti_role=lti_role
        )

        return user

    @pytest.fixture()
    def course(self, db_session, application_instance):
        course = factories.Course(application_instance=application_instance)
        db_session.flush()
        return course

    @pytest.fixture
    def matching_params(self, assignment):
        return {
            "tool_consumer_instance_guid": assignment.tool_consumer_instance_guid,
            "resource_link_id": assignment.resource_link_id,
        }

    @pytest.fixture(params=["tool_consumer_instance_guid", "resource_link_id"])
    def non_matching_params(self, request, matching_params):
        non_matching_params = dict(matching_params)
        non_matching_params[request.param] = "NOT_MATCHING"

        return non_matching_params

    @pytest.fixture(autouse=True)
    def with_assignment_noise(self, assignment):
        return [
            factories.Assignment(
                tool_consumer_instance_guid=assignment.tool_consumer_instance_guid,
                resource_link_id="noise_resource_link_id",
            ),
            factories.Assignment(
                tool_consumer_instance_guid="noise_tool_consumer_instance_guid",
                resource_link_id=assignment.resource_link_id,
            ),
        ]

    @pytest.fixture
    def create_assignment(self, svc):
        with patch.object(svc, "create_assignment", autospec=True) as patched:
            yield patched

    @pytest.fixture
    def get_assignment(self, svc):
        with patch.object(svc, "get_assignment", autospec=True) as patched:
            yield patched

    @pytest.fixture
    def _get_copied_from_assignment(self, svc):
        with patch.object(svc, "_get_copied_from_assignment", autospec=True) as patched:
            yield patched


class TestFactory:
    def test_it(self, pyramid_request, AssignmentService, misc_plugin):
        svc = factory(sentinel.context, pyramid_request)

        AssignmentService.assert_called_once_with(
            db=pyramid_request.db, misc_plugin=misc_plugin
        )
        assert svc == AssignmentService.return_value

    @pytest.fixture
    def AssignmentService(self, patch):
        return patch("lms.services.assignment.AssignmentService")
