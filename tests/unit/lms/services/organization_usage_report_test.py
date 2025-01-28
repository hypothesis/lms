from datetime import date, datetime, timedelta
from unittest.mock import patch, sentinel

import pytest
from freezegun import freeze_time
from h_matchers import Any

from lms.services.h_api import HAPI
from lms.services.organization_usage_report import (
    OrganizationUsageReportService,
    UsageReportRow,
    service_factory,
)
from tests import factories


class TestOrganizationUsageReportService:
    def test_get(self, svc, org_with_parent):
        report = factories.OrganizationUsageReport(
            organization=org_with_parent,
            key=f"{org_with_parent.public_id}-test-2020-01-01-2020-02-02",
            tag="test",
        )

        assert (
            svc.get(org_with_parent, "test", date(2020, 1, 1), date(2020, 2, 2))
            == report
        )

    def test_get_by_key(self, svc, org_with_parent):
        key = f"{org_with_parent.public_id}-test-2020-01-01-2020-02-02"
        report = factories.OrganizationUsageReport(
            organization=org_with_parent, key=key, tag="test"
        )

        assert svc.get_by_key(key) == report

    def test_generate_usage_report(
        self, svc, org_with_parent, usage_report, organization_service
    ):
        organization_service.get_by_id.return_value = org_with_parent
        usage_report.return_value = [
            UsageReportRow(
                name="<STUDENT>",
                email="<STUDENT>",
                h_userid=sentinel.h_userid,
                course_name=sentinel.lms_name,
                course_created="2020-01-01",
                authority_provided_id=sentinel.authority_provided_id,
            ),
            UsageReportRow(
                name="<STUDENT>",
                email="<STUDENT>",
                h_userid=sentinel.h_userid,
                course_name=sentinel.lms_name,
                course_created="2020-01-01",
                authority_provided_id=sentinel.authority_provided_id,
            ),
            UsageReportRow(
                name="Mr Teacher",
                email="teacher@example.com",
                h_userid=sentinel.h_userid_teacher,
                course_name=sentinel.lms_name,
                course_created="2020-01-01",
                authority_provided_id=sentinel.authority_provided_id,
            ),
        ]

        report = svc.generate_usage_report(
            org_with_parent.id, "test", "2020-01-01", "2020-02-02"
        )

        usage_report.assert_called_once_with(
            org_with_parent, "2020-01-01", "2020-02-02"
        )

        assert report.organization == org_with_parent
        assert report.unique_users == 2
        assert report.unique_teachers == 1
        assert report.since == "2020-01-01"
        assert report.until == "2020-02-02"
        assert len(report.report) == 3

    def test_generate_usage_report_empty_report_for_ValueError(
        self, svc, usage_report, org_with_parent, organization_service
    ):
        organization_service.get_by_id.return_value = org_with_parent
        usage_report.side_effect = ValueError

        report = svc.generate_usage_report(
            org_with_parent.id, "test", date(2020, 1, 1), date(2020, 2, 2)
        )

        assert not report.unique_users
        assert not report.report

    def test_generate_usage_report_existing_report(
        self, svc, org_with_parent, organization_service
    ):
        organization_service.get_by_id.return_value = org_with_parent

        report = factories.OrganizationUsageReport(
            organization=org_with_parent,
            key=f"{org_with_parent.public_id}-test-2020-01-01-2020-02-02",
            tag="test",
        )

        assert (
            svc.generate_usage_report(
                org_with_parent.id, "test", "2020-01-01", "2020-02-02"
            )
            == report
        )

    def test_usage_report(self, svc, org_with_parent, h_api, organization_service):
        since = datetime(2023, 1, 1, 0, 0, 0, 0)  # noqa: DTZ001
        until = datetime(2023, 12, 31, 23, 59, 59, 999999)  # noqa: DTZ001

        ai_root_org = factories.ApplicationInstance(organization=org_with_parent.parent)
        ai_child_org = factories.ApplicationInstance(organization=org_with_parent)
        course_root = factories.Course(
            application_instance=ai_root_org,
            created=since + timedelta(days=1),
        )
        section = factories.CanvasSection(
            application_instance=ai_root_org,
            parent=course_root,
            created=since + timedelta(days=1),
        )
        course_child = factories.Course(
            application_instance=ai_child_org, created=since + timedelta(days=1)
        )
        # Course created after the until date
        factories.Course(
            application_instance=ai_child_org,
            created=until + timedelta(days=1),
        )
        # Annotations in one section and in the other course
        h_api.get_groups.return_value = [
            HAPI.HAPIGroup(authority_provided_id=group.authority_provided_id)
            for group in [section, course_child]
        ]
        # Users that belong to the course
        user_1 = factories.User(display_name="NAME", email="EMAIL")
        user_2 = factories.User()
        factories.GroupingMembership(
            user=user_1, grouping=course_child, created=since + timedelta(days=1)
        )
        factories.GroupingMembership(
            user=user_2, grouping=course_root, created=since + timedelta(days=1)
        )
        organization_service.get_hierarchy_ids.return_value = [
            org_with_parent.parent.id,
            org_with_parent.id,
        ]

        report = svc.usage_report(org_with_parent.parent, since, until)

        h_api.get_groups.assert_called_once_with(
            Any.list.containing(
                [
                    course_root.authority_provided_id,
                    course_child.authority_provided_id,
                    section.authority_provided_id,
                ]
            ),
            since,
            until,
        )

        # We expect to get both users belonging to each course
        expected = [
            UsageReportRow(
                name=user_1.display_name,
                email=user_1.email,
                h_userid=user_1.h_userid,
                course_name=course_child.lms_name,
                course_created=course_child.created.date().isoformat(),
                authority_provided_id=course_child.authority_provided_id,
            ),
            UsageReportRow(
                name="<STUDENT>",
                email="<STUDENT>",
                h_userid=user_2.h_userid,
                course_name=course_root.lms_name,
                course_created=course_root.created.date().isoformat(),
                authority_provided_id=course_root.authority_provided_id,
            ),
        ]
        assert report == Any.list.containing(expected)

    def test_usage_report_with_no_courses(self, svc, org_with_parent):
        since = datetime(2023, 1, 1)  # noqa: DTZ001
        until = datetime(2023, 12, 31)  # noqa: DTZ001

        with pytest.raises(ValueError) as error:  # noqa: PT011
            svc.usage_report(org_with_parent.parent, since, until)

        assert "no courses found" in str(error.value).lower()

    def test_usage_report_with_no_activity(
        self, svc, org_with_parent, h_api, organization_service
    ):
        organization_service.get_hierarchy_ids.return_value = [
            org_with_parent.parent.id,
            org_with_parent.id,
        ]

        since = datetime(2023, 1, 1)  # noqa: DTZ001
        until = datetime(2023, 12, 31)  # noqa: DTZ001

        ai_root_org = factories.ApplicationInstance(organization=org_with_parent.parent)
        factories.Course(
            application_instance=ai_root_org, created=since + timedelta(days=1)
        )
        h_api.get_groups.return_value = []

        with pytest.raises(ValueError) as error:  # noqa: PT011
            svc.usage_report(org_with_parent.parent, since, until)

        assert "no courses with activity" in str(error.value).lower()

    @pytest.mark.parametrize(
        "now,deal_start,deal_end,reports,expected",
        [
            (
                # Before 2023, no reports
                "2024-06-07",
                date(2022, 11, 1),
                date(2024, 11, 1),
                1,
                [],
            ),
            (
                # Limit to 1, just from the deal start to last month end
                "2024-06-07",
                date(2023, 11, 1),
                date(2024, 11, 1),
                1,
                [(date(2023, 11, 1), date(2024, 5, 31))],
            ),
            (
                # Limit to 1, current date is past the deal's end
                "2025-01-05",
                date(2023, 11, 1),
                date(2024, 11, 15),
                1,
                [(date(2023, 11, 1), date(2024, 11, 15))],
            ),
            (
                # Not event a month between deal start and last month end
                "2023-11-20",
                date(2023, 11, 1),
                date(2024, 11, 1),
                1,
                [],
            ),
            (
                # Generate all reports possible
                "2024-03-20",
                date(2023, 11, 1),
                date(2024, 11, 1),
                1000,
                [
                    (date(2023, 11, 1), date(2024, 2, 29)),
                    (date(2023, 11, 1), date(2024, 1, 31)),
                    (date(2023, 11, 1), date(2023, 12, 31)),
                    (date(2023, 11, 1), date(2023, 11, 30)),
                ],
            ),
        ],
    )
    def test_monthly_report_dates(
        self, svc, now, deal_start, deal_end, reports, expected
    ):
        with freeze_time(now):
            result = svc.monthly_report_dates(deal_start, deal_end, reports)
            assert expected == result

    @pytest.fixture
    def org_with_parent(self, db_session):
        org_with_parent = factories.Organization.create(
            parent=factories.Organization.create()
        )
        # Flush to ensure public ids are generated
        db_session.flush()
        return org_with_parent

    @pytest.fixture
    def svc(self, db_session, h_api, organization_service):
        return OrganizationUsageReportService(
            db=db_session,
            h_api=h_api,
            organization_service=organization_service,
        )

    @pytest.fixture
    def usage_report(self, svc):
        with patch.object(svc, "usage_report") as usage_report:
            yield usage_report


class TestServiceFactory:
    def test_it(
        self,
        pyramid_request,
        OrganizationUsageReportService,
        h_api,
        organization_service,
    ):
        svc = service_factory(sentinel.context, pyramid_request)

        OrganizationUsageReportService.assert_called_once_with(
            db=pyramid_request.db,
            h_api=h_api,
            organization_service=organization_service,
        )
        assert svc == OrganizationUsageReportService.return_value

    @pytest.fixture
    def OrganizationUsageReportService(self, patch):
        return patch(
            "lms.services.organization_usage_report.OrganizationUsageReportService"
        )
