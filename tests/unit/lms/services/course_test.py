from unittest.mock import create_autospec, sentinel

import pytest

from lms.models import Grouping
from lms.product.plugin import CourseServicePlugin
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

    def test_upsert_course(self, svc, grouping_service, application_instance, plugin):
        course = svc.upsert_course(
            context_id=sentinel.context_id,
            name=sentinel.name,
            extra=sentinel.extra,
        )

        plugin.get_new_course_settings.assert_called_once_with(
            settings=application_instance.settings,
            authority_provided_id=grouping_service.get_authority_provided_id.return_value,
        )

        grouping_service.upsert_groupings.assert_called_once_with(
            [
                {
                    "lms_id": sentinel.context_id,
                    "lms_name": sentinel.name,
                    "extra": sentinel.extra,
                    "settings": plugin.get_new_course_settings.return_value,
                }
            ],
            type_=Grouping.Type.COURSE,
        )

        assert course == grouping_service.upsert_groupings.return_value[0]

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
    def svc(self, db_session, application_instance, grouping_service, plugin):
        return CourseService(
            db=db_session,
            application_instance=application_instance,
            grouping_service=grouping_service,
            plugin=plugin,
        )

    @pytest.fixture
    def plugin(self):
        return create_autospec(CourseServicePlugin, instance=True, spec_set=True)


class TestCourseServiceFactory:
    @pytest.mark.usefixtures("with_plugins")
    def test_it(
        self,
        pyramid_request,
        application_instance_service,
        grouping_service,
        CourseService,
    ):
        svc = course_service_factory(sentinel.context, pyramid_request)

        application_instance_service.get_current.assert_called_once_with()

        CourseService.assert_called_once_with(
            db=pyramid_request.db,
            application_instance=application_instance_service.get_current.return_value,
            grouping_service=grouping_service,
            plugin=pyramid_request.product.plugin.course_service,
        )

        assert svc == CourseService.return_value

    @pytest.fixture
    def CourseService(self, patch):
        return patch("lms.services.course.CourseService")
