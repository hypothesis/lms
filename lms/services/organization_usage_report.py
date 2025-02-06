from dataclasses import asdict, dataclass
from datetime import date, datetime
from logging import getLogger

from dateutil.relativedelta import relativedelta
from sqlalchemy import Date, func, select
from sqlalchemy.orm import Session, aliased

from lms.models import (
    ApplicationInstance,
    Grouping,
    GroupingMembership,
    Organization,
    OrganizationUsageReport,
    User,
)
from lms.services.h_api import HAPI
from lms.services.organization import OrganizationService

LOG = getLogger(__name__)


@dataclass
class UsageReportRow:
    name: str | None
    email: str | None
    h_userid: str

    course_name: str
    course_created: datetime
    authority_provided_id: str

    @property
    def is_teacher(self):
        """Wether this row refers to a teacher."""
        # Consider anyone for which we have an email a teacher
        return self.email != "<STUDENT>"


class OrganizationUsageReportService:
    def __init__(
        self,
        db: Session,
        h_api: HAPI,
        organization_service: OrganizationService,
    ):
        self._db = db
        self._organization_service = organization_service
        self._h_api = h_api

    def get(
        self, organization, tag, since: date, until: date
    ) -> OrganizationUsageReport | None:
        key = OrganizationUsageReport.generate_key(organization, tag, since, until)
        return self.get_by_key(key)

    @staticmethod
    def monthly_report_dates(
        deal_start: date, deal_end: date, reports: int = 1
    ) -> list[tuple[date, date]]:
        """Get a list of dates for which we should generate report.

        Get tuples of dates (since, until) from the end of last month (or deal_end if already finished)
        until deal_start month by month.

        Generate at most `reports` reports.
        """
        if deal_start < date(2023, 1, 1):
            # We only generate this type of report from 2023
            return []

        reports_dates = []

        # First report, based on current date
        until = date.today()  # noqa: DTZ011

        for _ in range(reports):
            # Always calculate until the start of the previous month
            # day=31 does the right thing for every month
            until = (until - relativedelta(months=1)) + relativedelta(day=31)
            # Never go over the deal's end
            until = min(until, deal_end)

            if until <= deal_start:
                # Don't go over the deal start date
                break

            reports_dates.append((deal_start, until))

        return reports_dates

    def get_by_key(self, key: str) -> OrganizationUsageReport | None:
        """Get a report by its unique key."""
        return self._db.query(OrganizationUsageReport).filter_by(key=key).one_or_none()

    def generate_usage_report(
        self, organization_id: int, tag: str, since: date, until: date
    ):
        """Generate and store an usage report for one organization."""
        organization = self._organization_service.get_by_id(organization_id)
        assert organization  # noqa: S101
        report_key = OrganizationUsageReport.generate_key(
            organization, tag, since, until
        )

        if report := self.get_by_key(report_key):
            LOG.debug("Report already exists, skipping generation. %s", report_key)
            return report

        report = OrganizationUsageReport(
            organization=organization,
            key=report_key,
            since=since,
            until=until,
            tag=tag,
        )
        self._db.add(report)

        try:
            report_rows = self.usage_report(organization, since, until)
        except ValueError:
            # We raise ValueError for empty reports
            # That's useful for an user facing UI but here just store the result
            report_rows = []

        report.unique_users = len({r.h_userid for r in report_rows})
        report.unique_teachers = len({r.h_userid for r in report_rows if r.is_teacher})
        report.report = [asdict(r) for r in report_rows]

        return report

    def usage_report(self, organization: Organization, since: date, until: date):
        # Organizations that are children of the current one.
        # It includes the current org ID.
        organization_children = self._organization_service.get_hierarchy_ids(
            organization.id, include_parents=False
        )
        # All the groups that can hold annotations (courses and segments) from this org
        groups_from_org = self._db.scalars(
            select(Grouping.authority_provided_id)
            .join(ApplicationInstance)
            .where(
                ApplicationInstance.organization_id.in_(organization_children),
                # If a group was created after the date we are interested, exclude it
                Grouping.created <= until,
            )
        ).all()

        if not groups_from_org:
            raise ValueError(f"No courses found for {organization.public_id}")  # noqa: EM102, TRY003

        LOG.info(
            "Generating report for %s based on %d candidate groups.",
            organization.public_id,
            len(groups_from_org),
        )
        # Of those groups, get the ones that do have annotations in the time period
        groups_with_annos = [
            group.authority_provided_id
            for group in self._h_api.get_groups(
                groups_from_org,
                datetime.combine(since, datetime.min.time()),  # Start of since date
                datetime.combine(until, datetime.max.time()),  # End of until date
            )
        ]
        if not groups_with_annos:
            raise ValueError(  # noqa: TRY003
                f"No courses with activity found for {organization.public_id}"  # noqa: EM102
            )

        # Based on those groups generate the usage report based on the definition of unique user:
        # Users that belong to a course in which there are annotations in the time period
        parent = aliased(Grouping)
        query = (
            select(
                User.display_name.label("name"),
                User.email.label("email"),
                User.h_userid.label("h_userid"),
                Grouping.lms_name.label("course_name"),
                func.date_trunc("day", Grouping.created)
                .cast(Date)
                .label("course_created"),
                Grouping.authority_provided_id,
            )
            .select_from(User)
            .join(GroupingMembership)
            .join(Grouping)
            .distinct()
            .where(
                Grouping.authority_provided_id.in_(
                    # The report is based in courses so we query either
                    # groupings with no parent (courses) or the parents of segments (courses)
                    select(
                        func.coalesce(
                            parent.authority_provided_id, Grouping.authority_provided_id
                        )
                    )
                    .select_from(Grouping)
                    .outerjoin(parent, Grouping.parent_id == parent.id)
                    .where(Grouping.authority_provided_id.in_(groups_with_annos))
                ),
                # We can't exactly know the state of membership in the past but we can
                # know if someone was added to the group after the date we are interested
                GroupingMembership.created <= until,
            )
        )
        return [
            UsageReportRow(
                # Students might have name but they never have email
                name=row.name if row.email else "<STUDENT>",
                email=row.email if row.email else "<STUDENT>",
                h_userid=row.h_userid,
                course_name=row.course_name,
                course_created=row.course_created.isoformat(),
                authority_provided_id=row.authority_provided_id,
            )
            for row in self._db.execute(query).all()
        ]


def service_factory(_context, request) -> OrganizationUsageReportService:
    return OrganizationUsageReportService(
        db=request.db,
        h_api=request.find_service(HAPI),
        organization_service=request.find_service(OrganizationService),
    )
